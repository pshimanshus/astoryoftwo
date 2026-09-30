"""Offline fake-client checks for the exact CLI bytes distributed in the patch."""
import base64
import importlib.util
import io
import json
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

from PIL import Image
import pytest


PACKAGE = Path(__file__).resolve().parents[1] / "tools/imagegen-skill-patch"


@pytest.fixture
def cli(monkeypatch, tmp_path):
    spec = importlib.util.spec_from_file_location("imagegen_patch", PACKAGE / "manage.py")
    manager = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(manager)
    _, payloads, _ = manager.load_package()
    module = ModuleType("imagegen_offline_test")
    exec(compile(payloads["scripts/image_gen.py"][1], "patched-image_gen.py", "exec"), module.__dict__)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "offline-test-sentinel")
    # Any unmocked network/client use is a test failure.
    def forbidden():
        pytest.fail("Client created before offline validation or without a fake")
    monkeypatch.setattr(module, "_create_client", forbidden)
    monkeypatch.setattr(module, "_create_async_client", forbidden)
    return module


def run(cli, monkeypatch, *args):
    monkeypatch.setattr(sys, "argv", ["image_gen.py", *map(str, args)])
    return cli.main()


def image_data():
    data = io.BytesIO()
    Image.new("RGBA", (8, 8), (10, 20, 30, 100)).save(data, format="PNG")
    return data.getvalue()


def response(n=1):
    return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(image_data()).decode()) for _ in range(n)])


def fake_sync(cli, monkeypatch, calls, callback=None):
    def request(**payload):
        calls.append(payload)
        if callback:
            callback(payload)
        return response(payload.get("n", 1))
    def create():
        calls.append("client")
        return SimpleNamespace(images=SimpleNamespace(generate=request, edit=request))
    monkeypatch.setattr(cli, "_create_client", create)


def jobs(path, values):
    path.write_text("\n".join(json.dumps(v) for v in values) + "\n")
    return path


@pytest.mark.parametrize("fmt", ["png", "webp"])
def test_default_model_accepts_preview_transparency_dryrun_without_writes(cli, monkeypatch, tmp_path, capsys, fmt):
    before = set(tmp_path.rglob("*"))
    run(cli, monkeypatch, "generate", "--prompt", "cutout", "--background", "transparent",
        "--output-format", fmt, "--out-dir", tmp_path / "new/out", "--dry-run")
    planned = json.loads(capsys.readouterr().out)
    assert planned["model"] == "gpt-image-2"
    assert planned["background"] == "transparent"
    assert planned["output_format"] == fmt
    assert set(tmp_path.rglob("*")) == before


def test_transparent_jpeg_is_rejected_before_client(cli, monkeypatch):
    with pytest.raises(SystemExit):
        run(cli, monkeypatch, "generate", "--prompt", "cutout", "--background", "transparent", "--output-format", "jpeg")


def test_gpt_image_2_input_fidelity_rejected_before_client(cli, monkeypatch, tmp_path):
    source = tmp_path / "input.png"
    source.write_bytes(image_data())
    with pytest.raises(SystemExit):
        run(cli, monkeypatch, "edit", "--image", source, "--prompt", "fix", "--input-fidelity", "high")


@pytest.mark.parametrize("command", ["generate", "edit"])
def test_ordered_input_references_use_edit_endpoint(cli, monkeypatch, tmp_path, command):
    files = [tmp_path / f"input-{i}.png" for i in range(3)]
    for i, path in enumerate(files):
        path.write_bytes(image_data() + bytes([i]))
    requests = []
    def edit(**payload):
        requests.append(([Path(f.name) for f in payload["image"]], [f.read() for f in payload["image"]]))
        return response()
    def generate(**_):
        pytest.fail("References were sent to text-only generate endpoint")
    monkeypatch.setattr(cli, "_create_client", lambda: SimpleNamespace(images=SimpleNamespace(edit=edit, generate=generate)))
    args = [command, "--prompt", "create a new scene" if command == "generate" else "fix the target", "--out", tmp_path / "result.png"]
    for path in files:
        args += ["--image", path]
    run(cli, monkeypatch, *args)
    assert requests == [(files, [p.read_bytes() for p in files])]
    assert (tmp_path / "result.png").read_bytes() == image_data()


@pytest.mark.parametrize("key", ["image", "images", "mask", "input_images", "image_url", "referenced_image_paths"])
def test_text_batch_rejects_image_bearing_jobs_before_client(cli, monkeypatch, tmp_path, key):
    path = jobs(tmp_path / "jobs.jsonl", [{"prompt": "safe first"}, {"prompt": "bad second", key: "input.png"}])
    with pytest.raises(SystemExit):
        run(cli, monkeypatch, "generate-batch", "--input", path, "--out-dir", tmp_path / "out")
    assert not (tmp_path / "out").exists()
    assert not (tmp_path / "tmp").exists()


@pytest.mark.parametrize("force", [False, True])
def test_batch_duplicate_outputs_reject_even_force(cli, monkeypatch, tmp_path, force):
    path = jobs(tmp_path / "jobs.jsonl", [{"prompt": "first", "out": "same.png"}, {"prompt": "second", "out": "same.png"}])
    with pytest.raises(SystemExit):
        run(cli, monkeypatch, "generate-batch", "--input", path, "--out-dir", tmp_path / "out", *(["--force"] if force else []))
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("force", [False, True])
def test_batch_derivative_collisions_reject_even_force(cli, monkeypatch, tmp_path, force):
    path = jobs(tmp_path / "jobs.jsonl", [{"prompt": "first", "out": "hero.png"}, {"prompt": "second", "out": "hero-web.png"}])
    with pytest.raises(SystemExit):
        run(cli, monkeypatch, "generate-batch", "--input", path, "--out-dir", tmp_path / "out", "--downscale-max-dim", 4, *(["--force"] if force else []))


def test_empty_downscale_suffix_rejects_duplicate_single_output(cli, monkeypatch):
    with pytest.raises(SystemExit):
        run(cli, monkeypatch, "generate", "--prompt", "thing", "--downscale-max-dim", 4, "--downscale-suffix", "", "--force")


@pytest.mark.parametrize("command", ["generate", "edit", "generate-batch"])
def test_existing_output_rejected_before_client(cli, monkeypatch, tmp_path, command):
    output = tmp_path / "exists.png"
    output.write_bytes(b"existing")
    if command == "generate-batch":
        path = jobs(tmp_path / "jobs.jsonl", [{"prompt": "first"}, {"prompt": "second", "out": "exists.png"}])
        args = [command, "--input", path, "--out-dir", tmp_path]
    else:
        args = [command, "--prompt", "thing", "--out", output]
        if command == "edit":
            source = tmp_path / "input.png"
            source.write_bytes(image_data())
            args += ["--image", source]
    with pytest.raises(SystemExit):
        run(cli, monkeypatch, *args)
    assert output.read_bytes() == b"existing"


def test_batch_validates_late_payload_before_client(cli, monkeypatch, tmp_path):
    path = jobs(tmp_path / "jobs.jsonl", [{"prompt": "first"}, {"prompt": "second", "size": "17x17"}])
    with pytest.raises(SystemExit):
        run(cli, monkeypatch, "generate-batch", "--input", path, "--out-dir", tmp_path / "out")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("command", ["edit", "generate-batch"])
def test_dryrun_never_writes_for_edit_or_batch(cli, monkeypatch, tmp_path, command):
    if command == "edit":
        source = tmp_path / "input.png"
        source.write_bytes(image_data())
        args = [command, "--prompt", "fix", "--image", source, "--out", tmp_path / "new/out.png"]
    else:
        path = jobs(tmp_path / "jobs.jsonl", [{"prompt": "first"}, {"prompt": "second", "n": 2}])
        args = [command, "--input", path, "--out-dir", tmp_path / "new/out"]
    before = set(tmp_path.rglob("*"))
    run(cli, monkeypatch, *args, "--dry-run", "--downscale-max-dim", 4)
    assert set(tmp_path.rglob("*")) == before


def test_response_originals_saved_before_promotion_and_success_cleans_recovery(cli, monkeypatch, tmp_path):
    calls = []
    fake_sync(cli, monkeypatch, calls)
    promote = cli._promote_bytes
    observed = []
    def inspect_then_promote(path, raw, *, force):
        original = list((tmp_path / "tmp/imagegen/recovery").rglob("original-*.png"))
        assert len(original) == 2
        assert all(p.read_bytes() == image_data() for p in original)
        observed.append(path)
        return promote(path, raw, force=force)
    monkeypatch.setattr(cli, "_promote_bytes", inspect_then_promote)
    run(cli, monkeypatch, "generate", "--prompt", "thing", "--n", 2, "--out", tmp_path / "result.png", "--downscale-max-dim", 4)
    assert len(observed) == 4
    assert not list((tmp_path / "tmp/imagegen/recovery").iterdir())
    with Image.open(tmp_path / "result-1-web.png") as img:
        assert img.size == (4, 4)
        assert img.mode == "RGBA"


def test_destination_race_retains_originals_without_api_retry(cli, monkeypatch, tmp_path):
    calls = []
    output = tmp_path / "result.png"
    fake_sync(cli, monkeypatch, calls, lambda _: output.write_bytes(b"raced"))
    with pytest.raises(cli.OutputWriteError, match="retained at"):
        run(cli, monkeypatch, "generate", "--prompt", "thing", "--out", output)
    assert output.read_bytes() == b"raced"
    assert len(calls) == 2  # one client, one paid request
    original = next((tmp_path / "tmp/imagegen/recovery").rglob("original-*.png"))
    assert original.read_bytes() == image_data()
    receipt = json.loads((original.parent / "recovery.json").read_text())
    assert receipt["promoted"] == []


def test_derivative_write_failure_preserves_originals_and_records_partial_promotion(cli, monkeypatch, tmp_path):
    calls = []
    fake_sync(cli, monkeypatch, calls)
    promote = cli._promote_bytes
    def fail_derived(path, raw, *, force):
        if path.name.endswith("-web.png"):
            raise OSError("injected disk failure")
        return promote(path, raw, force=force)
    monkeypatch.setattr(cli, "_promote_bytes", fail_derived)
    with pytest.raises(cli.OutputWriteError, match="disk failure"):
        run(cli, monkeypatch, "generate", "--prompt", "thing", "--out", tmp_path / "result.png", "--downscale-max-dim", 4)
    receipt_path = next((tmp_path / "tmp/imagegen/recovery").rglob("recovery.json"))
    assert json.loads(receipt_path.read_text())["promoted"] == [str(tmp_path / "result.png")]
    assert (receipt_path.parent / "original-001.png").read_bytes() == image_data()
    assert len(calls) == 2


def test_async_batch_write_failure_does_not_retry_generation(cli, monkeypatch, tmp_path):
    calls = []
    async def generate(**payload):
        calls.append(payload)
        return response()
    monkeypatch.setattr(cli, "_create_async_client", lambda: SimpleNamespace(images=SimpleNamespace(generate=generate)))
    def fail(*_, **__):
        raise OSError("disk down")
    monkeypatch.setattr(cli, "_promote_bytes", fail)
    path = jobs(tmp_path / "jobs.jsonl", [{"prompt": "first"}])
    with pytest.raises(SystemExit) as exc:
        run(cli, monkeypatch, "generate-batch", "--input", path, "--out-dir", tmp_path / "out", "--max-attempts", 3)
    assert exc.value.code == 1
    assert len(calls) == 1
    assert len(list((tmp_path / "tmp/imagegen/recovery").rglob("original-*.png"))) == 1


def test_mismatched_image_count_retains_every_return_before_promotion(cli, monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "_create_client", lambda: SimpleNamespace(images=SimpleNamespace(generate=lambda **_: response(2))))
    with pytest.raises(cli.OutputWriteError, match="received 2"):
        run(cli, monkeypatch, "generate", "--prompt", "thing", "--out", tmp_path / "result.png")
    assert not (tmp_path / "result.png").exists()
    assert len(list((tmp_path / "tmp/imagegen/recovery").rglob("original-*.png"))) == 2


def test_force_allows_existing_file_replacement(cli, monkeypatch, tmp_path):
    calls = []
    fake_sync(cli, monkeypatch, calls)
    output = tmp_path / "result.png"
    output.write_bytes(b"old")
    run(cli, monkeypatch, "generate", "--prompt", "thing", "--out", output, "--force")
    assert output.read_bytes() == image_data()


@pytest.mark.parametrize("extra", [{"fields": {"image": "ref.png"}}, {"payload": {"mask": "mask.png"}}, {"mask_file": "mask.png"}])
def test_nested_or_unrecognized_inputs_are_not_silently_discarded(cli, monkeypatch, tmp_path, extra):
    path = jobs(tmp_path / "jobs.jsonl", [{"prompt": "new scene", **extra}])
    with pytest.raises(SystemExit):
        run(cli, monkeypatch, "generate-batch", "--input", path, "--out-dir", tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_recovery_write_failure_does_not_claim_originals_were_saved(cli, monkeypatch, tmp_path):
    calls = []
    fake_sync(cli, monkeypatch, calls)
    durable_write = cli._durable_write
    def fail_response(path, raw):
        if path.name == "response.json":
            raise OSError("recovery disk full")
        return durable_write(path, raw)
    monkeypatch.setattr(cli, "_durable_write", fail_response)
    with pytest.raises(cli.OutputWriteError, match="complete response could not be saved"):
        run(cli, monkeypatch, "generate", "--prompt", "thing", "--out", tmp_path / "result.png")
    receipt = json.loads(next((tmp_path / "tmp/imagegen/recovery").rglob("recovery.json")).read_text())
    assert receipt["complete_response_saved"] is False
    assert receipt["saved_originals"] == []
    assert not (tmp_path / "result.png").exists()
    assert len(calls) == 2
