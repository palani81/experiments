import Foundation

/// Detects project paths from sessions that aren't yet configured.
public struct ProjectDiscovery {

    /// Given all session project paths and configured projects,
    /// return unique paths that are not yet configured.
    public static func findUnconfiguredPaths(
        sessionPaths: [String?],
        configuredProjects: [Project]
    ) -> [String] {
        let configuredPaths = Set(configuredProjects.map { normalizePath($0.path) })

        // Collect unique non-nil session paths
        var seen = Set<String>()
        var unconfigured: [String] = []

        for rawPath in sessionPaths {
            guard let rawPath, !rawPath.isEmpty else { continue }
            let normalized = normalizePath(rawPath)
            guard !seen.contains(normalized) else { continue }
            seen.insert(normalized)

            // Skip if this path matches a configured project or is a subdirectory of one
            if configuredPaths.contains(normalized) { continue }
            if isSubdirectory(normalized, ofAny: configuredPaths) { continue }

            unconfigured.append(rawPath)
        }

        return unconfigured.sorted()
    }

    /// Normalize a path: expand ~, resolve symlinks, remove trailing slash.
    static func normalizePath(_ path: String) -> String {
        var p = (path as NSString).expandingTildeInPath
        while p.hasSuffix("/") && p.count > 1 {
            p = String(p.dropLast())
        }
        return p
    }

    /// Check if `path` is a subdirectory of any path in `parents`.
    private static func isSubdirectory(_ path: String, ofAny parents: Set<String>) -> Bool {
        for parent in parents {
            if path.hasPrefix(parent + "/") {
                return true
            }
        }
        return false
    }
}
