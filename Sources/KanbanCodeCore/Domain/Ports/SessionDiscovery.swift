import Foundation

/// Port for discovering Claude Code sessions across all projects.
public protocol SessionDiscovery: Sendable {
    /// Discover all sessions, returning metadata for each.
    func discoverSessions() async throws -> [Session]

    /// Incremental re-scan: only sessions modified since last scan.
    func discoverNewOrModified(since: Date) async throws -> [Session]
}
