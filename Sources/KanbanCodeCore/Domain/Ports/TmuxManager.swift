import Foundation

/// Port for managing tmux sessions.
public protocol TmuxManagerPort: Sendable {
    /// List all tmux sessions.
    func listSessions() async throws -> [TmuxSession]

    /// Create a new tmux session.
    func createSession(name: String, path: String, command: String?) async throws

    /// Kill a tmux session by name.
    func killSession(name: String) async throws

    /// Find the tmux session for a worktree using matching heuristics.
    func findSessionForWorktree(
        sessions: [TmuxSession],
        worktreePath: String,
        branch: String?
    ) -> TmuxSession?

    /// Send literal text + Enter to a tmux session (for submitting prompts).
    func sendPrompt(to sessionName: String, text: String) async throws

    /// Paste text via tmux load-buffer + paste-buffer, then press Enter.
    /// Uses bracketed paste which bypasses readline special character handling
    /// (e.g. Gemini CLI treats `?` as a special command in send-keys mode).
    func pastePrompt(to sessionName: String, text: String) async throws

    /// Capture the visible contents of a tmux pane.
    func capturePane(sessionName: String) async throws -> String

    /// Send an empty bracketed paste event to trigger Claude Code's clipboard check.
    func sendBracketedPaste(to sessionName: String) async throws

    /// Check if tmux is available on this system.
    func isAvailable() async -> Bool
}
