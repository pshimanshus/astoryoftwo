import AppKit
import Foundation

struct BrandLabelManifest: Decodable {
    let input_image: String
    let output_image: String
    let labels: [BrandLabel]
}

struct BrandLabel: Decodable {
    let x: CGFloat
    let y: CGFloat
    let width: CGFloat
    let height: CGFloat
    let corner_radius: CGFloat?
    let fill: String
    let stroke: String?
    let text_color: String
    let font_size: CGFloat
    let lines: [String]
}

func color(from hex: String, alpha: CGFloat = 1.0) -> NSColor {
    var value = hex.trimmingCharacters(in: CharacterSet(charactersIn: "#"))
    if value.count == 3 {
        value = value.map { "\($0)\($0)" }.joined()
    }
    let scanner = Scanner(string: value)
    var rgb: UInt64 = 0
    scanner.scanHexInt64(&rgb)
    return NSColor(
        calibratedRed: CGFloat((rgb >> 16) & 0xff) / 255.0,
        green: CGFloat((rgb >> 8) & 0xff) / 255.0,
        blue: CGFloat(rgb & 0xff) / 255.0,
        alpha: alpha
    )
}

func savePNG(_ rep: NSBitmapImageRep, to path: String) throws {
    guard let data = rep.representation(using: .png, properties: [:]) else {
        throw NSError(domain: "brand-label-renderer", code: 1, userInfo: [NSLocalizedDescriptionKey: "Could not encode PNG"])
    }
    try data.write(to: URL(fileURLWithPath: path))
}

func drawLabel(_ label: BrandLabel, imageHeight: CGFloat) {
    let rect = CGRect(
        x: label.x,
        y: imageHeight - label.y - label.height,
        width: label.width,
        height: label.height
    )
    let radius = label.corner_radius ?? min(label.width, label.height) * 0.08
    let path = NSBezierPath(roundedRect: rect, xRadius: radius, yRadius: radius)
    color(from: label.fill, alpha: 0.93).setFill()
    path.fill()
    if let stroke = label.stroke {
        color(from: stroke, alpha: 0.28).setStroke()
        path.lineWidth = 1.2
        path.stroke()
    }

    let font = NSFont(name: "Futura-Medium", size: label.font_size)
        ?? NSFont(name: "Arial Rounded MT Bold", size: label.font_size)
        ?? NSFont.boldSystemFont(ofSize: label.font_size)
    let paragraph = NSMutableParagraphStyle()
    paragraph.alignment = .center
    paragraph.lineSpacing = label.font_size * 0.12
    let attributes: [NSAttributedString.Key: Any] = [
        .font: font,
        .foregroundColor: color(from: label.text_color),
        .paragraphStyle: paragraph,
        .kern: 0.45,
    ]
    let text = label.lines.joined(separator: "\n")
    let textRect = rect.insetBy(dx: label.width * 0.08, dy: label.height * 0.11)
    (text as NSString).draw(
        with: textRect,
        options: [.usesLineFragmentOrigin, .usesFontLeading],
        attributes: attributes
    )
}

do {
    guard CommandLine.arguments.count == 2 else {
        throw NSError(
            domain: "brand-label-renderer",
            code: 2,
            userInfo: [NSLocalizedDescriptionKey: "Usage: swift scripts/render_brand_product_labels.swift <manifest.json>"]
        )
    }
    let manifestURL = URL(fileURLWithPath: CommandLine.arguments[1])
    let data = try Data(contentsOf: manifestURL)
    let manifest = try JSONDecoder().decode(BrandLabelManifest.self, from: data)
    guard let image = NSImage(contentsOfFile: manifest.input_image) else {
        throw NSError(
            domain: "brand-label-renderer",
            code: 3,
            userInfo: [NSLocalizedDescriptionKey: "Could not read image: \(manifest.input_image)"]
        )
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
        throw NSError(domain: "brand-label-renderer", code: 4, userInfo: [NSLocalizedDescriptionKey: "Could not create bitmap"])
    }

    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
    image.draw(in: CGRect(x: 0, y: 0, width: width, height: height))
    for label in manifest.labels {
        drawLabel(label, imageHeight: CGFloat(height))
    }
    NSGraphicsContext.restoreGraphicsState()

    try FileManager.default.createDirectory(
        at: URL(fileURLWithPath: manifest.output_image).deletingLastPathComponent(),
        withIntermediateDirectories: true
    )
    try savePNG(rep, to: manifest.output_image)
    print(manifest.output_image)
} catch {
    fputs("render_brand_product_labels.swift: \(error)\n", stderr)
    exit(1)
}
