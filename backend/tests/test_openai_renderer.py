import base64
import unittest
from unittest.mock import MagicMock

from app.providers.openai_renderer import OpenAIRenderer


def _resp(png: bytes):
    r = MagicMock()
    item = MagicMock()
    item.b64_json = base64.b64encode(png).decode()
    r.data = [item]
    return r


class RendererTests(unittest.TestCase):
    def test_generate_when_no_refs(self):
        client = MagicMock()
        client.images.generate.return_value = _resp(b"PNGBYTES")
        r = OpenAIRenderer(api_key="k", model="gpt-image-1", client=client)
        out = r.render("draw them", [], "1024x1536")
        self.assertEqual(out, b"PNGBYTES")
        client.images.generate.assert_called_once()
        self.assertFalse(client.images.edit.called)
        self.assertEqual(client.images.generate.call_args.kwargs["model"], "gpt-image-1")
        self.assertEqual(client.images.generate.call_args.kwargs["size"], "1024x1536")

    def test_edit_when_refs_present(self):
        client = MagicMock()
        client.images.edit.return_value = _resp(b"EDITED")
        r = OpenAIRenderer(api_key="k", model="gpt-image-1", client=client)
        out = r.render("restyle", [b"refimg"], "1024x1536")
        self.assertEqual(out, b"EDITED")
        client.images.edit.assert_called_once()
        self.assertFalse(client.images.generate.called)
