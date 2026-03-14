import Foundation

/// A git worktree on disk.
public struct Worktree: Identifiable, Sendable {
    public var id: String { path }
    public let path: String
    public let branch: String?
    public let isBare: Bool

    public init(path: String, branch: String?, isBare: Bool = false) {
        self.path = path
        self.branch = branch
        self.isBare = isBare
    }

    /// The last path component (directory name).
    public var directoryName: String {
        (path as NSString).lastPathComponent
    }
}
