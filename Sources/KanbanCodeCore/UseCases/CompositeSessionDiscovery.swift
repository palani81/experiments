import Foundation

/// A `SessionDiscovery` implementation that wraps the registry, calls all
/// registered assistant discoveries, and merges results sorted by modification
/// time descending. If one assistant's discovery fails, it logs the error and
/// continues with the others.
public final class CompositeSessionDiscovery: SessionDiscovery, @unchecked Sendable {
    private let registry: CodingAssistantRegistry

    public init(registry: CodingAssistantRegistry) {
        self.registry = registry
    }

    public func discoverSessions() async throws -> [Session] {
        var allSessions: [Session] = []

        for assistant in registry.available {
            guard let discovery = registry.discovery(for: assistant) else { continue }
            do {
                let sessions = try await discovery.discoverSessions()
                allSessions.append(contentsOf: sessions)
            } catch {
                KanbanCodeLog.warn(
                    "composite-discovery",
                    "discoverSessions failed for \(assistant.displayName): \(error)"
                )
            }
        }

        return allSessions.sorted { $0.modifiedTime > $1.modifiedTime }
    }

    public func discoverNewOrModified(since date: Date) async throws -> [Session] {
        var allSessions: [Session] = []

        for assistant in registry.available {
            guard let discovery = registry.discovery(for: assistant) else { continue }
            do {
                let sessions = try await discovery.discoverNewOrModified(since: date)
                allSessions.append(contentsOf: sessions)
            } catch {
                KanbanCodeLog.warn(
                    "composite-discovery",
                    "discoverNewOrModified failed for \(assistant.displayName): \(error)"
                )
            }
        }

        return allSessions.sorted { $0.modifiedTime > $1.modifiedTime }
    }
}
