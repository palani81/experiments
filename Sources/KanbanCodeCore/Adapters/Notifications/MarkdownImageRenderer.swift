import Foundation

#if os(macOS) || os(Linux)

/// Renders Markdown text to a dark-themed PNG image using pandoc + wkhtmltoimage.
/// Mirrors the rendering pipeline from claude-pushover.
public enum MarkdownImageRenderer {

    /// Check if the rendering pipeline is available.
    public static func isAvailable() async -> Bool {
        async let pandoc = ShellCommand.isAvailable("pandoc")
        async let wkhtmltoimage = ShellCommand.isAvailable("wkhtmltoimage")
        let p = await pandoc
        let w = await wkhtmltoimage
        return p && w
    }

    /// Render markdown text to a PNG image.
    /// Returns nil if the pipeline is unavailable or rendering fails.
    public static func renderToImage(markdown: String) async -> Data? {
        guard await isAvailable() else { return nil }

        let tmpDir = NSTemporaryDirectory()
        let id = UUID().uuidString
        let htmlPath = (tmpDir as NSString).appendingPathComponent("kanban-code-\(id).html")
        let imgPath = (tmpDir as NSString).appendingPathComponent("kanban-code-\(id).png")

        defer {
            try? FileManager.default.removeItem(atPath: htmlPath)
            try? FileManager.default.removeItem(atPath: imgPath)
        }

        do {
            // Convert markdown → HTML body fragment with pandoc (no --standalone)
            guard let pandocPath = ShellCommand.findExecutable("pandoc") else { return nil }
            let pandocResult = try await ShellCommand.run(
                pandocPath,
                arguments: ["-f", "gfm", "-t", "html"],
                stdin: markdown
            )
            guard pandocResult.succeeded else {
                KanbanCodeLog.error("markdown-render", "pandoc failed: \(pandocResult.stderr)")
                return nil
            }

            // Build complete HTML document with dark theme CSS + pandoc body
            let html = htmlTemplate.replacingOccurrences(of: "{{BODY}}", with: pandocResult.stdout)
            try html.write(toFile: htmlPath, atomically: true, encoding: .utf8)

            // Render HTML → PNG with wkhtmltoimage
            guard let wkhtmlPath = ShellCommand.findExecutable("wkhtmltoimage") else { return nil }
            let imgResult = try await ShellCommand.run(
                wkhtmlPath,
                arguments: ["--quality", "90",
                           "--width", "600",
                           "--disable-smart-width",
                           "--quiet",
                           htmlPath, imgPath]
            )
            guard imgResult.succeeded else {
                KanbanCodeLog.error("markdown-render", "wkhtmltoimage failed: \(imgResult.stderr)")
                return nil
            }

            return try Data(contentsOf: URL(fileURLWithPath: imgPath))
        } catch {
            KanbanCodeLog.error("markdown-render", "render failed: \(error)")
            return nil
        }
    }

    // MARK: - Private

    private static let htmlTemplate = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        font-size: 14px;
        line-height: 1.5;
        color: #e0e0e0;
        background-color: #1e1e1e;
        padding: 20px;
        max-width: 600px;
        margin: 0;
    }
    pre, code {
        background-color: #2d2d2d;
        border-radius: 4px;
        font-family: 'SF Mono', Monaco, 'Courier New', monospace;
        font-size: 13px;
    }
    pre {
        padding: 12px;
        overflow-x: auto;
    }
    code {
        padding: 2px 6px;
    }
    pre code {
        padding: 0;
        background: none;
    }
    h1, h2, h3, h4 { color: #fff; margin-top: 1em; }
    a { color: #58a6ff; }
    blockquote {
        border-left: 3px solid #444;
        margin-left: 0;
        padding-left: 16px;
        color: #aaa;
    }
    hr { border: none; border-top: 1px solid #444; }
    table { border-collapse: collapse; }
    th, td { border: 1px solid #444; padding: 8px; }
    th { background-color: #2d2d2d; }
    </style>
    </head>
    <body>
    {{BODY}}
    </body>
    </html>
    """
}

#else

/// Stub for platforms where pandoc/wkhtmltoimage are not available.
public enum MarkdownImageRenderer {
    public static func isAvailable() async -> Bool { false }
    public static func renderToImage(markdown: String) async -> Data? { nil }
}

#endif
