import Foundation

/// Runs shell commands and returns their output.
public enum ShellCommand {

    public struct Result: Sendable {
        public let exitCode: Int32
        public let stdout: String
        public let stderr: String

        public var succeeded: Bool { exitCode == 0 }
    }

#if os(macOS) || os(Linux)
    /// Cached user login-shell environment, resolved once on first use.
    private static let userEnvironment: [String: String] = {
        let shell = ProcessInfo.processInfo.environment["SHELL"] ?? "/bin/zsh"
        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: shell)
        proc.arguments = ["-l", "-c", "env"]
        let pipe = Pipe()
        proc.standardOutput = pipe
        proc.standardError = Pipe()
        do {
            try proc.run()
            let data = pipe.fileHandleForReading.readDataToEndOfFile()
            proc.waitUntilExit()
            guard proc.terminationStatus == 0,
                  let output = String(data: data, encoding: .utf8) else {
                return ProcessInfo.processInfo.environment
            }
            var env: [String: String] = [:]
            for line in output.components(separatedBy: "\n") {
                guard let eq = line.firstIndex(of: "=") else { continue }
                let key = String(line[..<eq])
                let value = String(line[line.index(after: eq)...])
                env[key] = value
            }
            return env.isEmpty ? ProcessInfo.processInfo.environment : env
        } catch {
            return ProcessInfo.processInfo.environment
        }
    }()

    /// Run a command and capture its output.
    public static func run(
        _ executable: String,
        arguments: [String] = [],
        currentDirectory: String? = nil,
        stdin: String? = nil
    ) async throws -> Result {
        let process = Process()
        process.executableURL = URL(fileURLWithPath: executable)
        process.arguments = arguments
        process.environment = userEnvironment

        if let dir = currentDirectory {
            process.currentDirectoryURL = URL(fileURLWithPath: dir)
        }

        let stdoutPipe = Pipe()
        let stderrPipe = Pipe()
        process.standardOutput = stdoutPipe
        process.standardError = stderrPipe

        if let stdin, let data = stdin.data(using: .utf8) {
            let stdinPipe = Pipe()
            process.standardInput = stdinPipe
            stdinPipe.fileHandleForWriting.write(data)
            stdinPipe.fileHandleForWriting.closeFile()
        }

        try process.run()

        let stdoutData = stdoutPipe.fileHandleForReading.readDataToEndOfFile()
        let stderrData = stderrPipe.fileHandleForReading.readDataToEndOfFile()

        process.waitUntilExit()

        return Result(
            exitCode: process.terminationStatus,
            stdout: String(data: stdoutData, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? "",
            stderr: String(data: stderrData, encoding: .utf8)?.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        )
    }

    /// Check if a command is available on the system.
    public static func isAvailable(_ command: String) async -> Bool {
        findExecutable(command) != nil
    }

    /// Resolve a command name to an absolute path.
    public static func findExecutable(_ command: String) -> String? {
        let home = NSHomeDirectory()
        var searchPaths = [
            "\(home)/.claude/local",
            "\(home)/.local/bin",
            "/opt/homebrew/bin",
            "/usr/local/bin",
            "/usr/bin",
            "/bin",
        ]

        if let userPath = userEnvironment["PATH"] {
            for dir in userPath.components(separatedBy: ":") where !dir.isEmpty {
                if !searchPaths.contains(dir) {
                    searchPaths.append(dir)
                }
            }
        }

        for dir in searchPaths {
            let path = "\(dir)/\(command)"
            if FileManager.default.isExecutableFile(atPath: path) {
                return path
            }
        }
        return nil
    }
#else
    // iOS stubs — shell execution is not available on iOS
    public static func run(
        _ executable: String,
        arguments: [String] = [],
        currentDirectory: String? = nil,
        stdin: String? = nil
    ) async throws -> Result {
        return Result(exitCode: 1, stdout: "", stderr: "Shell commands not available on iOS")
    }

    public static func isAvailable(_ command: String) async -> Bool {
        return false
    }

    public static func findExecutable(_ command: String) -> String? {
        return nil
    }
#endif
}
