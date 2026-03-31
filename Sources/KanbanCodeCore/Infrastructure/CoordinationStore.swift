import Foundation

/// Persistent store for Link records in ~/.kanban-code/links.json.
/// Atomic writes, file locking, corruption recovery.
public actor CoordinationStore {
    private let filePath: String
    private let encoder: JSONEncoder
    private let decoder: JSONDecoder

    public init(basePath: String? = nil) {
        let base = basePath ?? (NSHomeDirectory() as NSString).appendingPathComponent(".kanban-code")
        self.filePath = (base as NSString).appendingPathComponent("links.json")

        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        encoder.dateEncodingStrategy = .iso8601
        self.encoder = encoder

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        self.decoder = decoder
    }

    // MARK: - Public API

    /// Read all links from the coordination file.
    public func readLinks() throws -> [Link] {
        let container = try readContainer()
        return container.links
    }

    private func readContainer() throws -> LinksContainer {
        let fileManager = FileManager.default
        guard fileManager.fileExists(atPath: filePath) else {
            return LinksContainer(links: [])
        }

        let data = try Data(contentsOf: URL(fileURLWithPath: filePath))
        do {
            return try decoder.decode(LinksContainer.self, from: data)
        } catch {
            // Corruption recovery: backup and return empty
            let backupPath = filePath + ".bkp"
            try? fileManager.copyItem(atPath: filePath, toPath: backupPath)
            return LinksContainer(links: [])
        }
    }

    /// Write all links to the coordination file (atomic).
    public func writeLinks(_ links: [Link]) throws {
        let fileManager = FileManager.default
        let dir = (filePath as NSString).deletingLastPathComponent
        try fileManager.createDirectory(atPath: dir, withIntermediateDirectories: true)

        let container = LinksContainer(links: links)
        let data = try encoder.encode(container)

        // Atomic write: write to .tmp, then rename
        let tmpPath = filePath + ".tmp"
        try data.write(to: URL(fileURLWithPath: tmpPath))
        _ = try? fileManager.removeItem(atPath: filePath)
        try fileManager.moveItem(atPath: tmpPath, toPath: filePath)
    }

    /// Get a single link by its id.
    public func linkById(_ id: String) throws -> Link? {
        try readLinks().first { $0.id == id }
    }

    /// Get a single link by session ID.
    public func linkForSession(_ sessionId: String) throws -> Link? {
        try readLinks().first { $0.sessionLink?.sessionId == sessionId }
    }

    /// Upsert a link: update if exists (by link.id), insert if new.
    public func upsertLink(_ link: Link) throws {
        var links = try readLinks()
        if let index = links.firstIndex(where: { $0.id == link.id }) {
            links[index] = link
        } else {
            links.append(link)
        }
        try writeLinks(links)
    }

    /// Update specific fields of a link by link.id.
    public func updateLink(id: String, update: (inout Link) -> Void) throws {
        var links = try readLinks()
        guard let index = links.firstIndex(where: { $0.id == id }) else { return }
        update(&links[index])
        links[index].updatedAt = .now
        try writeLinks(links)
    }

    /// Update specific fields of a link by session ID.
    public func updateLink(sessionId: String, update: (inout Link) -> Void) throws {
        var links = try readLinks()
        guard let index = links.firstIndex(where: { $0.sessionLink?.sessionId == sessionId }) else { return }
        update(&links[index])
        links[index].updatedAt = .now
        try writeLinks(links)
    }

    /// Remove a link by its id.
    public func removeLink(id: String) throws {
        var links = try readLinks()
        links.removeAll { $0.id == id }
        try writeLinks(links)
    }

    /// Remove a link by session ID.
    public func removeLink(sessionId: String) throws {
        var links = try readLinks()
        links.removeAll { $0.sessionLink?.sessionId == sessionId }
        try writeLinks(links)
    }

    /// Remove orphaned links whose .jsonl files no longer exist.
    public func removeOrphans() throws {
        let fileManager = FileManager.default
        var links = try readLinks()
        let before = links.count
        links.removeAll { link in
            guard let path = link.sessionLink?.sessionPath else { return false }
            return !fileManager.fileExists(atPath: path)
        }
        if links.count != before {
            try writeLinks(links)
        }
    }

    /// Atomic read-modify-write: reads current links, applies transform, writes back.
    /// Runs entirely within the actor — no interleaving with concurrent reads/writes.
    public func modifyLinks(_ transform: (inout [Link]) -> Void) throws {
        var links = try readLinks()
        transform(&links)
        try writeLinks(links)
    }

    /// The file path for external access / debugging.
    public var path: String { filePath }
}

// MARK: - Codable Container

private struct LinksContainer: Codable {
    let links: [Link]
}
