import Foundation

#if os(macOS) || os(Linux)

/// Watches ~/.kanban-code/remote/status-*.json files for remote connection status changes.
/// Posts notifications via a NotifierPort when a host goes offline or comes back online.
public final class RemoteStatusWatcher: @unchecked Sendable {
    private let stateDir: String
    private let notifier: NotifierPort?
    private var knownStatuses: [String: RemoteHostStatus] = [:]
    private let statusLock = NSLock()

    /// Lightweight representation of a host's connection status.
    private struct RemoteHostStatus: Sendable {
        let status: String // "online" or "offline"
        let since: String? // ISO 8601 timestamp for offline, nil for online
    }

    public init(
        stateDir: String? = nil,
        notifier: NotifierPort? = nil
    ) {
        self.stateDir = stateDir
            ?? (NSHomeDirectory() as NSString).appendingPathComponent(".kanban-code/remote")
        self.notifier = notifier
    }

    /// Check if a given host is currently online.
    /// Returns `true` if no status file exists (assume online by default).
    public func isOnline(host: String) -> Bool {
        let filePath = statusFilePath(for: host)
        guard let data = try? Data(contentsOf: URL(fileURLWithPath: filePath)),
              let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let status = json["status"] as? String else {
            return true // No status file = assume online
        }
        return status == "online"
    }

    /// Poll all status files and notify on changes.
    /// Call this periodically (e.g. from BackgroundOrchestrator tick).
    public func pollStatusChanges() async {
        let fm = FileManager.default
        guard let files = try? fm.contentsOfDirectory(atPath: stateDir) else { return }

        let statusFiles = files.filter { $0.hasPrefix("status-") && $0.hasSuffix(".json") }

        for file in statusFiles {
            // Extract host from filename: status-<host>.json
            let name = (file as NSString).deletingPathExtension // "status-<host>"
            let host = String(name.dropFirst("status-".count))
            guard !host.isEmpty else { continue }

            let filePath = (stateDir as NSString).appendingPathComponent(file)
            guard let data = try? Data(contentsOf: URL(fileURLWithPath: filePath)),
                  let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let status = json["status"] as? String else { continue }

            let since = json["since"] as? String
            let current = RemoteHostStatus(status: status, since: since)

            let previous: RemoteHostStatus?
            previous = statusLock.withLock {
                let prev = knownStatuses[host]
                knownStatuses[host] = current
                return prev
            }

            // Detect changes and notify
            if let prev = previous, prev.status != current.status {
                await notifyStatusChange(host: host, newStatus: current.status)
            } else if previous == nil && current.status == "offline" {
                // First poll and already offline — notify
                await notifyStatusChange(host: host, newStatus: current.status)
            }
        }
    }

    // MARK: - Private

    private func statusFilePath(for host: String) -> String {
        (stateDir as NSString).appendingPathComponent("status-\(host).json")
    }

    private func notifyStatusChange(host: String, newStatus: String) async {
        guard let notifier else { return }

        let title: String
        let message: String

        if newStatus == "offline" {
            title = "Remote Connection Lost"
            message = "Remote connection to \(host) lost \u{2014} using local fallback"
        } else {
            title = "Remote Connection Restored"
            message = "Remote connection to \(host) restored"
        }

        try? await notifier.sendNotification(title: title, message: message, imageData: nil, cardId: nil)
    }
}

#endif
