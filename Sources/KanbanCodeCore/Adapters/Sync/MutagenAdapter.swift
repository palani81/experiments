import Foundation

/// Manages Mutagen sync sessions via the mutagen CLI.
public final class MutagenAdapter: SyncManagerPort, @unchecked Sendable {
    private let label: String
    private let mutagenPath: String

    /// Default ignore patterns for mutagen sync (matching claude-remote + Swift/Rust).
    public static let defaultIgnores: [String] = [
        "node_modules", ".venv", ".cache", "dist", ".next*",
        "__pycache__", ".pytest_cache", ".mypy_cache", ".turbo",
        "*.pyc", ".DS_Store", "coverage", ".nyc_output",
        "target", "build", ".build", ".swiftpm",
    ]

    public init(label: String = "kanban") {
        self.label = label
        self.mutagenPath = ShellCommand.findExecutable("mutagen") ?? "mutagen"
    }

    public func startSync(localPath: String, remotePath: String, name: String, ignores: [String] = MutagenAdapter.defaultIgnores) async throws {
        // Check for ANY existing kanban sync session — there should only ever be one
        // since we use a single global remote config.
        let listResult = try? await ShellCommand.run(
            mutagenPath,
            arguments: ["sync", "list", "--label-selector", "\(label)=true"]
        )
        if let listResult, listResult.succeeded, listResult.stdout.contains("Name:") {
            // Already running — just flush and return
            try? await flushSync()
            return
        }

        var args = [
            "sync", "create",
            localPath, remotePath,
            "--name", name,
            "--label", "\(label)=true",
            "--sync-mode", "two-way-resolved",
            "--default-file-mode-beta", "0644",
            "--default-directory-mode-beta", "0755",
        ]
        for pattern in ignores {
            args.append(contentsOf: ["--ignore", pattern])
        }

        let result = try await ShellCommand.run(mutagenPath, arguments: args)
        if !result.succeeded {
            throw MutagenError.createFailed(name: name, message: result.stderr)
        }
    }

    /// Reset a stuck or errored sync session by pausing then resuming.
    public func resetSync(name: String) async throws {
        let selector = "--label-selector"
        let labelFilter = "\(label)=true"
        _ = try await ShellCommand.run(mutagenPath, arguments: ["sync", "pause", selector, labelFilter])
        let result = try await ShellCommand.run(mutagenPath, arguments: ["sync", "resume", selector, labelFilter])
        if !result.succeeded {
            throw MutagenError.resetFailed(message: result.stderr)
        }
    }

    public func stopSync(name: String) async throws {
        let result = try await ShellCommand.run(
            mutagenPath,
            arguments: ["sync", "terminate", "--label-selector", "\(label)=true"]
        )
        if !result.succeeded {
            throw MutagenError.terminateFailed(name: name, message: result.stderr)
        }
    }

    public func flushSync() async throws {
        let result = try await ShellCommand.run(
            mutagenPath,
            arguments: ["sync", "flush", "--label-selector", "\(label)=true"]
        )
        if !result.succeeded {
            throw MutagenError.flushFailed(message: result.stderr)
        }
    }

    public func status() async throws -> [String: SyncStatus] {
        let template = #"{{range .}}{{.Name}}|{{.Status}}|{{len .Conflicts}}|{{.Paused}}{{"\\n"}}{{end}}"#
        let result = try await ShellCommand.run(
            mutagenPath,
            arguments: [
                "sync", "list",
                "--label-selector", "\(label)=true",
                "--template", template,
            ]
        )

        guard result.succeeded, !result.stdout.isEmpty else { return [:] }

        var statuses: [String: SyncStatus] = [:]
        for line in result.stdout.split(separator: "\n") {
            let parts = line.split(separator: "|", maxSplits: 3)
            guard parts.count >= 4 else { continue }
            let name = String(parts[0])
            let statusStr = String(parts[1]).lowercased()
            let conflictCount = Int(parts[2]) ?? 0
            let paused = String(parts[3]) == "true"

            let status: SyncStatus
            if paused {
                status = .paused
            } else if conflictCount > 0 {
                status = .conflicts
            } else {
                switch statusStr {
                case "watching": status = .watching
                case "scanning", "staging", "transitioning", "reconciling", "saving": status = .staging
                case "halted": status = .paused
                default: status = .error
                }
            }
            statuses[name] = status
        }

        return statuses
    }

    public func rawStatus() async throws -> String {
        let result = try await ShellCommand.run(
            mutagenPath,
            arguments: ["sync", "list", "-l"]
        )
        let output = result.stdout.trimmingCharacters(in: .whitespacesAndNewlines)
        if output.isEmpty {
            return "No sync sessions running."
        }
        return output
    }

    public func isAvailable() async -> Bool {
        ShellCommand.findExecutable("mutagen") != nil
    }
}

public enum MutagenError: Error, LocalizedError {
    case createFailed(name: String, message: String)
    case terminateFailed(name: String, message: String)
    case resetFailed(message: String)
    case flushFailed(message: String)

    public var errorDescription: String? {
        switch self {
        case .createFailed(let name, let msg): "Failed to create sync '\(name)': \(msg)"
        case .terminateFailed(let name, let msg): "Failed to terminate sync '\(name)': \(msg)"
        case .resetFailed(let msg): "Failed to reset sync: \(msg)"
        case .flushFailed(let msg): "Failed to flush sync: \(msg)"
        }
    }
}
