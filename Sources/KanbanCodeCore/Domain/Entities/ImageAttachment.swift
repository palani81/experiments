import Foundation

/// A transient image attachment for prompt dialogs.
/// Not persisted in links.json — images are saved as temp files for queued prompts.
public struct ImageAttachment: Identifiable, Sendable {
    public let id: String
    public let data: Data
    public var tempPath: String?

    public init(id: String = UUID().uuidString, data: Data, tempPath: String? = nil) {
        self.id = id
        self.data = data
        self.tempPath = tempPath
    }

    /// Save image data to a temp file. Returns the path.
    @discardableResult
    public mutating func saveToTemp() throws -> String {
        let path = "/tmp/kanban-code-img-\(id).png"
        try data.write(to: URL(fileURLWithPath: path))
        tempPath = path
        return path
    }

    /// Save image data to persistent storage (~/.kanban-code/images/). Returns the path.
    @discardableResult
    public mutating func saveToPersistent() throws -> String {
        let dir = (NSHomeDirectory() as NSString).appendingPathComponent(".kanban-code/images")
        try FileManager.default.createDirectory(atPath: dir, withIntermediateDirectories: true)
        let path = (dir as NSString).appendingPathComponent("\(id).png")
        try data.write(to: URL(fileURLWithPath: path))
        tempPath = path
        return path
    }

    /// Load an ImageAttachment from a temp file path.
    public static func fromPath(_ path: String) -> ImageAttachment? {
        guard let data = try? Data(contentsOf: URL(fileURLWithPath: path)) else { return nil }
        return ImageAttachment(data: data, tempPath: path)
    }
}
