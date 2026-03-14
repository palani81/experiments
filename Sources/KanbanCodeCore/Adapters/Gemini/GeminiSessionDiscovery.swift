import Foundation

/// Discovers Gemini CLI sessions by reading `~/.gemini/projects.json` for slug→path mapping
/// and scanning `~/.gemini/tmp/<slug>/chats/session-*.json` files.
public final class GeminiSessionDiscovery: SessionDiscovery, @unchecked Sendable {
    private let geminiDir: String
    private var lastScanTime: Date?

    /// Cache: sessionId → parsed session
    private var cachedSessions: [String: Session] = [:]
    /// Per-chats-directory mtime to skip unchanged slug dirs
    private var dirMtimes: [String: Date] = [:]
    /// Per-file mtime to skip unchanged session files
    private var fileMtimes: [String: Date] = [:]
    /// Track which sessions came from which slug for eviction
    private var slugSessionIds: [String: Set<String>] = [:]

    public init(geminiDir: String? = nil) {
        self.geminiDir = geminiDir
            ?? (NSHomeDirectory() as NSString).appendingPathComponent(".gemini")
    }

    // MARK: - SessionDiscovery

    public func discoverSessions() async throws -> [Session] {
        let fileManager = FileManager.default
        guard fileManager.fileExists(atPath: geminiDir) else { return [] }

        let slugToPath = readProjectsMapping()

        let tmpDir = (geminiDir as NSString).appendingPathComponent("tmp")
        guard fileManager.fileExists(atPath: tmpDir) else { return [] }

        let slugDirs: [String]
        do {
            slugDirs = try fileManager.contentsOfDirectory(atPath: tmpDir)
        } catch {
            return []
        }

        var seenSlugs: Set<String> = []

        for slug in slugDirs {
            let chatsDir = (tmpDir as NSString)
                .appendingPathComponent(slug)
                .appending("/chats")

            var isDir: ObjCBool = false
            guard fileManager.fileExists(atPath: chatsDir, isDirectory: &isDir),
                  isDir.boolValue else {
                continue
            }
            seenSlugs.insert(slug)

            // Check directory mtime — skip if unchanged
            let dirAttrs = try? fileManager.attributesOfItem(atPath: chatsDir)
            let dirMtime = dirAttrs?[.modificationDate] as? Date
            if let cached = dirMtimes[slug], dirMtime == cached {
                continue
            }
            dirMtimes[slug] = dirMtime

            let projectPath = resolveProjectPath(slug: slug, slugToPath: slugToPath)

            let files: [String]
            do {
                files = try fileManager.contentsOfDirectory(atPath: chatsDir)
            } catch {
                continue
            }

            let sessionFiles = files.filter {
                $0.hasPrefix("session-") && $0.hasSuffix(".json")
            }

            var slugSessions: Set<String> = []

            for fileName in sessionFiles {
                let filePath = (chatsDir as NSString).appendingPathComponent(fileName)

                guard let attrs = try? fileManager.attributesOfItem(atPath: filePath),
                      let mtime = attrs[.modificationDate] as? Date else {
                    continue
                }

                // Extract session ID for cache key
                let sessionId: String
                if let cached = cachedSessions.values.first(where: { $0.jsonlPath == filePath }) {
                    sessionId = cached.id
                    slugSessions.insert(sessionId)

                    if let cachedMtime = fileMtimes[filePath], mtime == cachedMtime {
                        continue
                    }
                } else {
                    // Will be determined after parsing
                    sessionId = ""
                }

                fileMtimes[filePath] = mtime

                do {
                    if let metadata = try GeminiSessionParser.extractMetadata(from: filePath) {
                        let session = Session(
                            id: metadata.sessionId,
                            name: metadata.summary,
                            firstPrompt: metadata.firstPrompt,
                            projectPath: projectPath,
                            messageCount: metadata.messageCount,
                            modifiedTime: mtime,
                            jsonlPath: filePath,
                            assistant: .gemini
                        )
                        cachedSessions[metadata.sessionId] = session
                        slugSessions.insert(metadata.sessionId)
                    }
                } catch {
                    continue
                }
            }

            // Evict sessions from this slug that no longer exist
            if let oldIds = slugSessionIds[slug] {
                for removedId in oldIds.subtracting(slugSessions) {
                    cachedSessions.removeValue(forKey: removedId)
                }
            }
            slugSessionIds[slug] = slugSessions
        }

        // Evict slugs that were removed
        for removedSlug in Set(dirMtimes.keys).subtracting(seenSlugs) {
            dirMtimes.removeValue(forKey: removedSlug)
            if let ids = slugSessionIds.removeValue(forKey: removedSlug) {
                for id in ids { cachedSessions.removeValue(forKey: id) }
            }
        }

        var sessions = Array(cachedSessions.values)
        sessions.sort { $0.modifiedTime > $1.modifiedTime }
        lastScanTime = Date()
        return sessions
    }

    public func discoverNewOrModified(since: Date) async throws -> [Session] {
        return try await discoverSessions()
    }

    // MARK: - Project Mapping

    /// Schema for `~/.gemini/projects.json`:
    /// ```json
    /// { "projects": { "/absolute/path": "slug" } }
    /// ```
    private struct ProjectsFile: Codable {
        let projects: [String: String] // path → slug
    }

    /// Read `~/.gemini/projects.json` and build a slug→path lookup.
    private func readProjectsMapping() -> [String: String] {
        let projectsPath = (geminiDir as NSString).appendingPathComponent("projects.json")
        guard let data = FileManager.default.contents(atPath: projectsPath) else {
            return [:]
        }

        do {
            let decoded = try JSONDecoder().decode(ProjectsFile.self, from: data)
            // Invert: projects.json maps path→slug, we need slug→path
            var slugToPath: [String: String] = [:]
            for (path, slug) in decoded.projects {
                slugToPath[slug] = path
            }
            return slugToPath
        } catch {
            return [:]
        }
    }

    /// Resolve a project path from a slug, using the projects.json mapping.
    /// Falls back to nil if no mapping exists.
    private func resolveProjectPath(slug: String, slugToPath: [String: String]) -> String? {
        return slugToPath[slug]
    }
}
