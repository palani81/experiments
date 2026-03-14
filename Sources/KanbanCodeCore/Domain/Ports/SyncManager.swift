import Foundation

/// Sync session status.
public enum SyncStatus: String, Sendable {
    case watching
    case staging
    case conflicts
    case paused
    case error
    case notRunning = "not_running"
}

/// Port for managing file synchronization (e.g., Mutagen).
public protocol SyncManagerPort: Sendable {
    /// Start sync for a project.
    func startSync(localPath: String, remotePath: String, name: String, ignores: [String]) async throws

    /// Stop sync for a project.
    func stopSync(name: String) async throws

    /// Flush pending sync changes.
    func flushSync() async throws

    /// Get current sync status.
    func status() async throws -> [String: SyncStatus]

    /// Get raw human-readable sync status output.
    func rawStatus() async throws -> String

    /// Check if sync tool is available.
    func isAvailable() async -> Bool
}
