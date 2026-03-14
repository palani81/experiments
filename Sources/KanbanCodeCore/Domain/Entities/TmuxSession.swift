import Foundation

/// A tmux session discovered via `tmux list-sessions`.
public struct TmuxSession: Identifiable, Sendable {
    public var id: String { name }
    public let name: String
    public let path: String // session_path
    public let attached: Bool

    public init(name: String, path: String, attached: Bool = false) {
        self.name = name
        self.path = path
        self.attached = attached
    }
}
