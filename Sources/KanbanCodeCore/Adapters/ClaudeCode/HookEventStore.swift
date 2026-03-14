import Foundation

/// Reads and manages hook events from ~/.kanban-code/hook-events.jsonl.
public actor HookEventStore {
    private let filePath: String
    private var lastReadOffset: UInt64 = 0

    public init(basePath: String? = nil) {
        let base = basePath ?? (NSHomeDirectory() as NSString).appendingPathComponent(".kanban-code")
        self.filePath = (base as NSString).appendingPathComponent("hook-events.jsonl")
    }

    /// Read new events since the last read.
    public func readNewEvents() throws -> [HookEvent] {
        guard FileManager.default.fileExists(atPath: filePath) else { return [] }

        let handle = try FileHandle(forReadingFrom: URL(fileURLWithPath: filePath))
        defer { try? handle.close() }

        handle.seek(toFileOffset: lastReadOffset)
        let data = handle.readDataToEndOfFile()
        lastReadOffset = handle.offsetInFile

        guard !data.isEmpty, let text = String(data: data, encoding: .utf8) else { return [] }

        let iso = ISO8601DateFormatter()
        return text.components(separatedBy: "\n").compactMap { line -> HookEvent? in
            guard !line.isEmpty,
                  let lineData = line.data(using: .utf8),
                  let obj = try? JSONSerialization.jsonObject(with: lineData) as? [String: Any],
                  let sessionId = obj["sessionId"] as? String else {
                return nil
            }

            let eventName = obj["event"] as? String ?? "unknown"
            let transcriptPath = obj["transcriptPath"] as? String
            let timestampStr = obj["timestamp"] as? String
            let timestamp = timestampStr.flatMap { iso.date(from: $0) } ?? Date()

            return HookEvent(
                sessionId: sessionId,
                eventName: eventName,
                transcriptPath: transcriptPath,
                timestamp: timestamp
            )
        }
    }

    /// Read all events (for initial load).
    public func readAllEvents() throws -> [HookEvent] {
        lastReadOffset = 0
        return try readNewEvents()
    }

    /// The file path.
    public var path: String { filePath }
}
