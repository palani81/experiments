import Foundation

/// Port for tracking GitHub pull requests.
public protocol PRTrackerPort: Sendable {
    /// Fetch all PRs for a repository, keyed by branch name.
    func fetchPRs(repoRoot: String) async throws -> [String: PullRequest]

    /// Enrich open PRs with CI checks and review thread counts.
    func enrichPRDetails(repoRoot: String, prs: inout [String: PullRequest]) async throws

    /// Fetch PR body on demand (lazy-loaded when user opens PR tab).
    func fetchPRBody(repoRoot: String, prNumber: Int) async throws -> String?

    /// Check if the gh CLI is available and authenticated.
    func isAvailable() async -> Bool
}
