import Foundation

/// Resolves a GitHub base URL (e.g. "https://github.com/owner/repo") from a local git repo.
/// Results are cached in memory — `git remote get-url origin` is local (reads .git/config) so it's
/// fast, but we still avoid repeated process spawns.
public actor GitRemoteResolver {
    public static let shared = GitRemoteResolver()

    private var cache: [String: String?] = [:]
    private let gitPath = ShellCommand.findExecutable("git") ?? "/usr/bin/git"

    /// Returns the GitHub base URL for a repo at the given path, or nil if not a GitHub repo.
    /// Example: "/Users/me/projects/langwatch" → "https://github.com/langwatch/langwatch"
    public func githubBaseURL(for projectPath: String) async -> String? {
        if let cached = cache[projectPath] {
            return cached
        }

        let result = try? await ShellCommand.run(
            gitPath,
            arguments: ["remote", "get-url", "origin"],
            currentDirectory: projectPath
        )

        let url: String?
        if let stdout = result?.stdout, result?.succeeded == true {
            url = Self.parseGitHubURL(from: stdout.trimmingCharacters(in: .whitespacesAndNewlines))
        } else {
            url = nil
        }

        cache[projectPath] = url
        return url
    }

    /// Construct a full issue URL: "https://github.com/owner/repo/issues/42"
    public static func issueURL(base: String, number: Int) -> String {
        "\(base)/issues/\(number)"
    }

    /// Construct a full PR URL: "https://github.com/owner/repo/pull/42"
    public static func prURL(base: String, number: Int) -> String {
        "\(base)/pull/\(number)"
    }

    /// Parse a git remote URL into a GitHub base URL.
    /// Handles: git@github.com:owner/repo.git, https://github.com/owner/repo.git, etc.
    static func parseGitHubURL(from remote: String) -> String? {
        // SSH: git@github.com:owner/repo.git
        if remote.contains("github.com:") {
            let parts = remote.components(separatedBy: "github.com:")
            guard parts.count == 2 else { return nil }
            let path = parts[1].replacingOccurrences(of: ".git", with: "")
            return "https://github.com/\(path)"
        }

        // HTTPS: https://github.com/owner/repo.git
        if remote.contains("github.com/") {
            var cleaned = remote
            if cleaned.hasSuffix(".git") {
                cleaned = String(cleaned.dropLast(4))
            }
            // Normalize to https
            if cleaned.hasPrefix("http://") {
                cleaned = "https://" + cleaned.dropFirst(7)
            }
            return cleaned
        }

        return nil
    }
}
