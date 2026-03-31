import Foundation

/// Centralized logging for Kanban Code — writes to ~/.kanban-code/logs/kanban-code.log.
/// Thread-safe, fire-and-forget. Use from anywhere in KanbanCodeCore or Kanban.
public enum KanbanCodeLog {

    private static let logDir: String = {
        let dir = (NSHomeDirectory() as NSString).appendingPathComponent(".kanban-code/logs")
        try? FileManager.default.createDirectory(atPath: dir, withIntermediateDirectories: true)
        return dir
    }()

    private static let logPath: String = {
        (logDir as NSString).appendingPathComponent("kanban-code.log")
    }()

    private static let queue = DispatchQueue(label: "kanban-code.log", qos: .utility)

    /// Log a message with a subsystem tag.
    /// Example: `KanbanCodeLog.info("reconciler", "Matched session \(id) to card \(cardId)")`
    public nonisolated static func info(_ subsystem: String, _ message: String) {
        write("INFO", subsystem, message)
    }

    /// Log a warning.
    public nonisolated static func warn(_ subsystem: String, _ message: String) {
        write("WARN", subsystem, message)
    }

    /// Log an error.
    public nonisolated static func error(_ subsystem: String, _ message: String) {
        write("ERROR", subsystem, message)
    }

    private nonisolated static func write(_ level: String, _ subsystem: String, _ message: String) {
        let timestamp = ISO8601DateFormatter().string(from: Date())
        let line = "[\(timestamp)] [\(level)] [\(subsystem)] \(message)\n"

        queue.async {
            if let handle = FileHandle(forWritingAtPath: logPath) {
                handle.seekToEndOfFile()
                handle.write(line.data(using: .utf8) ?? Data())
                handle.closeFile()
            } else {
                FileManager.default.createFile(atPath: logPath, contents: line.data(using: .utf8))
            }
        }
    }
}
