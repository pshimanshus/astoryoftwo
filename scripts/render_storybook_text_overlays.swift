import AppKit
import Foundation

struct OverlayManifest: Decodable {
    let typography: [String: JSONValue]?
    let composition_role: String?
    let renderer: [String: String]
    let slides: [SlideRecord]
}

enum JSONValue: Codable {
    case string(String)
    case int(Int)
    case double(Double)
    case bool(Bool)

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()
        if let value = try? container.decode(String.self) {
            self = .string(value)
        } else if let value = try? container.decode(Int.self) {
            self = .int(value)
        } else if let value = try? container.decode(Double.self) {
            self = .double(value)
        } else if let value = try? container.decode(Bool.self) {
            self = .bool(value)
        } else {
            self = .string("")
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()
        switch self {
        case .string(let value):
            try container.encode(value)
        case .int(let value):
            try container.encode(value)
        case .double(let value):
            try container.encode(value)
        case .bool(let value):
            try container.encode(value)
        }
    }
}

struct SlideRecord: Decodable {
    let slide: Int
    let text: String
    let brandmark: String
    let placement: String?
    let text_layout: TextLayout?
}

struct TextLayout: Decodable {
    let primary_position: String?
    let speech_bubble: String?
}

struct RenderedSlide: Encodable {
    let slide: Int
    let source: String
    let file: String
}

struct RenderResult: Encodable {
    let status: String
    let composition_role: String?
    let typography: [String: JSONValue]?
    let renderer: [String: String]
    let slides: [RenderedSlide]
}

func readManifest(_ path: String) throws -> OverlayManifest {
    let data = try Data(contentsOf: URL(fileURLWithPath: path))
    return try JSONDecoder().decode(OverlayManifest.self, from: data)
}

func savePNG(_ rep: NSBitmapImageRep, to path: String) throws {
    guard let data = rep.representation(using: .png, properties: [:]) else {
        throw NSError(domain: "storybook-integrated-text", code: 1, userInfo: [NSLocalizedDescriptionKey: "Could not encode PNG: \(path)"])
    }
    try data.write(to: URL(fileURLWithPath: path))
}

func textSize(_ text: String, width: CGFloat, attributes: [NSAttributedString.Key: Any]) -> CGSize {
    let rect = (text as NSString).boundingRect(
        with: CGSize(width: width, height: 10000),
        options: [.usesLineFragmentOrigin, .usesFontLeading],
        attributes: attributes
    )
    return CGSize(width: ceil(rect.width), height: ceil(rect.height))
}

func drawText(_ text: String, rect: CGRect, attributes: [NSAttributedString.Key: Any]) {
    (text as NSString).draw(
        with: rect,
        options: [.usesLineFragmentOrigin, .usesFontLeading],
        attributes: attributes
    )
}

func drawPrimaryText(_ text: String, position: String, width: CGFloat, height: CGFloat) {
    let fontSize = max(39, width * 0.044)
    let font = NSFont(name: "Noteworthy-Light", size: fontSize)
        ?? NSFont(name: "BradleyHandITCTT-Bold", size: fontSize)
        ?? NSFont.systemFont(ofSize: fontSize)
    let paragraph = NSMutableParagraphStyle()
    paragraph.alignment = position.contains("center") ? .center : .left
    paragraph.lineSpacing = fontSize * 0.28
    let attributes: [NSAttributedString.Key: Any] = [
        .font: font,
        .foregroundColor: NSColor(calibratedRed: 0.08, green: 0.075, blue: 0.07, alpha: 1),
        .paragraphStyle: paragraph,
        .kern: 1.2,
    ]
    let maxWidth = width * (position.contains("center") ? 0.78 : 0.62)
    let size = textSize(text, width: maxWidth, attributes: attributes)
    let x = position.contains("center") ? (width - maxWidth) / 2 : width * 0.095
    let y: CGFloat
    if position.contains("bottom") {
        y = max(height * 0.095, height * 0.16)
    } else {
        y = height - height * 0.13 - size.height
    }
    drawText(text, rect: CGRect(x: x, y: y, width: maxWidth, height: size.height + fontSize), attributes: attributes)
}

func drawBrandmark(_ text: String, width: CGFloat, height: CGFloat) {
    let fontSize = max(23, width * 0.025)
    let font = NSFont(name: "Noteworthy-Light", size: fontSize)
        ?? NSFont(name: "BradleyHandITCTT-Bold", size: fontSize)
        ?? NSFont.systemFont(ofSize: fontSize)
    let attributes: [NSAttributedString.Key: Any] = [
        .font: font,
        .foregroundColor: NSColor(calibratedRed: 0.48, green: 0.41, blue: 0.34, alpha: 0.75),
        .kern: 1.0,
    ]
    let size = textSize(text, width: width * 0.36, attributes: attributes)
    drawText(
        text,
        rect: CGRect(x: width - width * 0.085 - size.width, y: height * 0.052, width: size.width + 8, height: size.height + 8),
        attributes: attributes
    )
}

func drawSpeechBubble(_ text: String, width: CGFloat, height: CGFloat) {
    guard !text.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
    let fontSize = max(28, width * 0.033)
    let font = NSFont(name: "Noteworthy-Light", size: fontSize)
        ?? NSFont(name: "BradleyHandITCTT-Bold", size: fontSize)
        ?? NSFont.systemFont(ofSize: fontSize)
    let paragraph = NSMutableParagraphStyle()
    paragraph.alignment = .center
    paragraph.lineSpacing = fontSize * 0.18
    let attributes: [NSAttributedString.Key: Any] = [
        .font: font,
        .foregroundColor: NSColor.black,
        .paragraphStyle: paragraph,
        .kern: 0.8,
    ]
    let bubbleWidth = width * 0.33
    let textBounds = textSize(text, width: bubbleWidth * 0.76, attributes: attributes)
    let bubbleHeight = max(height * 0.1, textBounds.height + fontSize * 1.25)
    let rect = CGRect(x: width * 0.16, y: height * 0.73, width: bubbleWidth, height: bubbleHeight)
    let path = NSBezierPath(roundedRect: rect, xRadius: bubbleHeight * 0.45, yRadius: bubbleHeight * 0.45)
    NSColor(calibratedWhite: 0.995, alpha: 0.82).setFill()
    path.fill()
    NSColor(calibratedWhite: 0.03, alpha: 1).setStroke()
    path.lineWidth = max(2.4, width * 0.0025)
    path.stroke()

    let tail = NSBezierPath()
    tail.move(to: CGPoint(x: rect.minX + bubbleWidth * 0.42, y: rect.minY + 3))
    tail.line(to: CGPoint(x: rect.minX + bubbleWidth * 0.48, y: rect.minY - height * 0.035))
    tail.line(to: CGPoint(x: rect.minX + bubbleWidth * 0.55, y: rect.minY + 8))
    NSColor(calibratedWhite: 0.995, alpha: 0.82).setFill()
    tail.fill()
    NSColor(calibratedWhite: 0.03, alpha: 1).setStroke()
    tail.lineWidth = max(2.4, width * 0.0025)
    tail.stroke()

    let textRect = CGRect(
        x: rect.minX + bubbleWidth * 0.12,
        y: rect.minY + (bubbleHeight - textBounds.height) / 2 - fontSize * 0.08,
        width: bubbleWidth * 0.76,
        height: textBounds.height + fontSize * 0.5
    )
    drawText(text, rect: textRect, attributes: attributes)
}

func renderSlide(carouselDir: String, record: SlideRecord) throws -> RenderedSlide {
    let number = String(format: "%02d", record.slide)
    let source = "\(carouselDir)/final/slide-\(number).png"
    let target = "\(carouselDir)/final-with-text/slide-\(number).png"
    guard let image = NSImage(contentsOfFile: source) else {
        throw NSError(domain: "storybook-integrated-text", code: 2, userInfo: [NSLocalizedDescriptionKey: "Could not read image: \(source)"])
    }
    let width = Int(image.size.width)
    let height = Int(image.size.height)
    guard let rep = NSBitmapImageRep(
        bitmapDataPlanes: nil,
        pixelsWide: width,
        pixelsHigh: height,
        bitsPerSample: 8,
        samplesPerPixel: 4,
        hasAlpha: true,
        isPlanar: false,
        colorSpaceName: .deviceRGB,
        bytesPerRow: 0,
        bitsPerPixel: 0
    ) else {
        throw NSError(domain: "storybook-integrated-text", code: 3, userInfo: [NSLocalizedDescriptionKey: "Could not create bitmap for: \(target)"])
    }

    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
    image.draw(in: CGRect(x: 0, y: 0, width: width, height: height))
    let layout = record.text_layout
    drawSpeechBubble(layout?.speech_bubble ?? "", width: CGFloat(width), height: CGFloat(height))
    drawPrimaryText(record.text, position: layout?.primary_position ?? "top_center", width: CGFloat(width), height: CGFloat(height))
    drawBrandmark(record.brandmark, width: CGFloat(width), height: CGFloat(height))
    NSGraphicsContext.restoreGraphicsState()

    try FileManager.default.createDirectory(
        atPath: "\(carouselDir)/final-with-text",
        withIntermediateDirectories: true
    )
    try savePNG(rep, to: target)
    return RenderedSlide(slide: record.slide, source: source, file: target)
}

do {
    guard CommandLine.arguments.count == 3 else {
        throw NSError(domain: "storybook-integrated-text", code: 4, userInfo: [NSLocalizedDescriptionKey: "Usage: render_storybook_text_overlays.swift <carousel_dir> <manifest_json>"])
    }
    let carouselDir = CommandLine.arguments[1]
    let manifest = try readManifest(CommandLine.arguments[2])
    let rendered = try manifest.slides.map { try renderSlide(carouselDir: carouselDir, record: $0) }
    let result = RenderResult(
        status: "rendered",
        composition_role: manifest.composition_role,
        typography: manifest.typography,
        renderer: manifest.renderer,
        slides: rendered
    )
    let data = try JSONEncoder().encode(result)
    try data.write(to: URL(fileURLWithPath: "\(carouselDir)/text-overlay.json"))
    try data.write(to: URL(fileURLWithPath: "\(carouselDir)/integrated-text-pass.json"))
    print(String(data: data, encoding: .utf8) ?? "{}")
} catch {
    fputs("render_storybook_text_overlays.swift: \(error)\n", stderr)
    exit(1)
}
