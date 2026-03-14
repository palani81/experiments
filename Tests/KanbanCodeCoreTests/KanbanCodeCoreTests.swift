import Testing
import Foundation
@testable import KanbanCodeCore

// MARK: - PRStatus Tests

@Suite("PRStatus")
struct PRStatusTests {
    @Test func comparableOrdering() {
        #expect(PRStatus.failing < PRStatus.approved)
        #expect(PRStatus.changesRequested < PRStatus.merged)
        #expect(PRStatus.approved < PRStatus.closed)
        #expect(PRStatus.unresolved < PRStatus.reviewNeeded)
    }

    @Test func priorityReflectsUrgency() {
        let sorted: [PRStatus] = [.merged, .failing, .approved, .changesRequested, .closed]
            .sorted()
        #expect(sorted == [.failing, .changesRequested, .approved, .merged, .closed])
    }

    @Test func rawValueRoundTrip() {
        #expect(PRStatus(rawValue: "changes_requested") == .changesRequested)
        #expect(PRStatus(rawValue: "review_needed") == .reviewNeeded)
        #expect(PRStatus(rawValue: "pending_ci") == .pendingCI)
        #expect(PRStatus(rawValue: "bogus") == nil)
    }
}

// MARK: - KanbanCodeColumn Tests

@Suite("KanbanCodeColumn")
struct KanbanCodeColumnTests {
    @Test func displayNames() {
        #expect(KanbanCodeColumn.backlog.displayName == "Backlog")
        #expect(KanbanCodeColumn.inProgress.displayName == "In Progress")
        #expect(KanbanCodeColumn.waiting.displayName == "Needs Attention")
        #expect(KanbanCodeColumn.inReview.displayName == "In Review")
        #expect(KanbanCodeColumn.done.displayName == "Done")
    }

    @Test func rawValueRoundTrip() {
        #expect(KanbanCodeColumn(rawValue: "in_progress") == .inProgress)
        #expect(KanbanCodeColumn(rawValue: "requires_attention") == .waiting)
        #expect(KanbanCodeColumn(rawValue: "in_review") == .inReview)
    }

    @Test func caseIterable() {
        #expect(KanbanCodeColumn.allCases.count == 6)
    }
}

// MARK: - TmuxLink Tests

@Suite("TmuxLink")
struct TmuxLinkTests {
    @Test func terminalCountWithoutExtras() {
        let link = TmuxLink(sessionName: "primary")
        #expect(link.terminalCount == 1)
        #expect(link.allSessionNames == ["primary"])
    }

    @Test func terminalCountWithExtras() {
        let link = TmuxLink(sessionName: "primary", extraSessions: ["shell-1", "shell-2"])
        #expect(link.terminalCount == 3)
        #expect(link.allSessionNames == ["primary", "shell-1", "shell-2"])
    }

    @Test func isShellOnlyStoredAsNilWhenFalse() {
        let link = TmuxLink(sessionName: "test", isShellOnly: false)
        #expect(link.isShellOnly == nil)
    }

    @Test func isShellOnlyStoredWhenTrue() {
        let link = TmuxLink(sessionName: "test", isShellOnly: true)
        #expect(link.isShellOnly == true)
    }
}

// MARK: - Link Tests

@Suite("Link")
struct LinkTests {
    @Test func displayTitlePriority() {
        // Name takes priority
        let withName = Link(name: "My Task", promptBody: "prompt", sessionLink: SessionLink(sessionId: "s1"))
        #expect(withName.displayTitle == "My Task")

        // PromptBody is next
        let withPrompt = Link(promptBody: "Do this thing", sessionLink: SessionLink(sessionId: "s1"))
        #expect(withPrompt.displayTitle == "Do this thing")

        // Branch is next
        let withBranch = Link(worktreeLink: WorktreeLink(path: "/p", branch: "feat/cool"))
        #expect(withBranch.displayTitle == "feat/cool")

        // PR title is next
        let withPR = Link(prLinks: [PRLink(number: 1, title: "Fix bug")])
        #expect(withPR.displayTitle == "Fix bug")

        // Session ID is next
        let withSession = Link(sessionLink: SessionLink(sessionId: "abc-123"))
        #expect(withSession.displayTitle == "abc-123")

        // Falls back to id
        let bare = Link(id: "card_xyz")
        #expect(bare.displayTitle == "card_xyz")
    }

    @Test func cardLabelDerivation() {
        let session = Link(sessionLink: SessionLink(sessionId: "s1"))
        #expect(session.cardLabel == .session)

        let worktree = Link(worktreeLink: WorktreeLink(path: "/p"))
        #expect(worktree.cardLabel == .worktree)

        let issue = Link(issueLink: IssueLink(number: 42))
        #expect(issue.cardLabel == .issue)

        let pr = Link(prLinks: [PRLink(number: 1)])
        #expect(pr.cardLabel == .pr)

        let task = Link()
        #expect(task.cardLabel == .task)
    }

    @Test func cardLabelPriorityOrder() {
        // session wins over worktree
        let both = Link(sessionLink: SessionLink(sessionId: "s"), worktreeLink: WorktreeLink(path: "/p"))
        #expect(both.cardLabel == .session)
    }

    @Test func prLinkComputedProperties() {
        let link = Link(prLinks: [
            PRLink(number: 1, status: .approved),
            PRLink(number: 2, status: .failing),
            PRLink(number: 3, status: .merged),
        ])
        #expect(link.prLink?.number == 1)
        #expect(link.worstPRStatus == .failing)
        #expect(link.allPRsDone == false)
    }

    @Test func allPRsDoneWhenAllMergedOrClosed() {
        let link = Link(prLinks: [
            PRLink(number: 1, status: .merged),
            PRLink(number: 2, status: .closed),
        ])
        #expect(link.allPRsDone == true)
    }

    @Test func allPRsDoneFalseWhenEmpty() {
        let link = Link()
        #expect(link.allPRsDone == false)
    }

    @Test func mergeableReturnsOnlyIfOneOpenPR() {
        let one = Link(prLinks: [PRLink(number: 1, status: .approved)])
        #expect(one.mergeablePR?.number == 1)

        let two = Link(prLinks: [PRLink(number: 1, status: .approved), PRLink(number: 2, status: .reviewNeeded)])
        #expect(two.mergeablePR == nil)

        let oneMerged = Link(prLinks: [PRLink(number: 1, status: .merged), PRLink(number: 2, status: .approved)])
        #expect(oneMerged.mergeablePR?.number == 2)
    }

    @Test func mergeBlockedValidation() {
        let a = Link(id: "a", sessionLink: SessionLink(sessionId: "s1"))
        let b = Link(id: "b", sessionLink: SessionLink(sessionId: "s2"))
        #expect(Link.mergeBlocked(source: a, target: b) != nil)

        // Same card
        #expect(Link.mergeBlocked(source: a, target: a) != nil)

        // Different issues
        let c = Link(id: "c", issueLink: IssueLink(number: 1))
        let d = Link(id: "d", issueLink: IssueLink(number: 2))
        #expect(Link.mergeBlocked(source: c, target: d) != nil)

        // Compatible: one has session, other has worktree
        let e = Link(id: "e", sessionLink: SessionLink(sessionId: "s"))
        let f = Link(id: "f", worktreeLink: WorktreeLink(path: "/p"))
        #expect(Link.mergeBlocked(source: e, target: f) == nil)
    }

    @Test func backwardCompatComputedProperties() {
        let link = Link(
            sessionLink: SessionLink(sessionId: "sid", sessionPath: "/path", sessionNumber: 3),
            tmuxLink: TmuxLink(sessionName: "tmux1"),
            worktreeLink: WorktreeLink(path: "/wt", branch: "main"),
            prLinks: [PRLink(number: 42)],
            issueLink: IssueLink(number: 7, body: "issue body")
        )
        #expect(link.sessionId == "sid")
        #expect(link.sessionPath == "/path")
        #expect(link.sessionNumber == 3)
        #expect(link.tmuxSession == "tmux1")
        #expect(link.worktreePath == "/wt")
        #expect(link.worktreeBranch == "main")
        #expect(link.githubPR == 42)
        #expect(link.githubIssue == 7)
        #expect(link.issueBody == "issue body")
    }

    @Test func jsonRoundTrip() throws {
        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601

        let original = Link(
            id: "card_test",
            name: "Test Card",
            projectPath: "/test",
            column: .inProgress,
            source: .hook,
            sessionLink: SessionLink(sessionId: "s1"),
            tmuxLink: TmuxLink(sessionName: "t1"),
            worktreeLink: WorktreeLink(path: "/wt", branch: "feat"),
            prLinks: [PRLink(number: 10, status: .approved)],
            issueLink: IssueLink(number: 5, title: "Bug")
        )
        let data = try encoder.encode(original)
        let decoded = try decoder.decode(Link.self, from: data)

        #expect(decoded.id == "card_test")
        #expect(decoded.name == "Test Card")
        #expect(decoded.column == .inProgress)
        #expect(decoded.source == .hook)
        #expect(decoded.sessionLink?.sessionId == "s1")
        #expect(decoded.tmuxLink?.sessionName == "t1")
        #expect(decoded.worktreeLink?.branch == "feat")
        #expect(decoded.prLinks.count == 1)
        #expect(decoded.prLinks.first?.status == .approved)
        #expect(decoded.issueLink?.number == 5)
    }

    @Test func legacyJsonDecoding() throws {
        // Simulate old flat format
        let json = """
        {
            "id": "card_legacy",
            "column": "in_progress",
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-01T00:00:00Z",
            "manualOverrides": {},
            "manuallyArchived": false,
            "source": "discovered",
            "isRemote": false,
            "sessionId": "legacy-session",
            "sessionPath": "/legacy/path",
            "tmuxSession": "legacy-tmux",
            "worktreePath": "/legacy/wt",
            "worktreeBranch": "legacy-branch",
            "githubPR": 99,
            "githubIssue": 42,
            "issueBody": "old issue body"
        }
        """
        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        let link = try decoder.decode(Link.self, from: Data(json.utf8))

        #expect(link.sessionLink?.sessionId == "legacy-session")
        #expect(link.sessionLink?.sessionPath == "/legacy/path")
        #expect(link.tmuxLink?.sessionName == "legacy-tmux")
        #expect(link.worktreeLink?.path == "/legacy/wt")
        #expect(link.worktreeLink?.branch == "legacy-branch")
        #expect(link.prLinks.first?.number == 99)
        #expect(link.issueLink?.number == 42)
        #expect(link.issueLink?.body == "old issue body")
    }
}

// MARK: - ManualOverrides Tests

@Suite("ManualOverrides")
struct ManualOverridesTests {
    @Test func isPRDismissedWithDismissedList() {
        let overrides = ManualOverrides(dismissedPRs: [10, 20])
        #expect(overrides.isPRDismissed(10) == true)
        #expect(overrides.isPRDismissed(30) == false)
    }

    @Test func isPRDismissedWithLegacyPrLinkFlag() {
        let overrides = ManualOverrides(prLink: true)
        #expect(overrides.isPRDismissed(999) == true)
    }

    @Test func isBranchDiscoveryBlocked() {
        let withWatermark = ManualOverrides(branchWatermark: 100)
        #expect(withWatermark.isBranchDiscoveryBlocked == true)

        let withWorktree = ManualOverrides(worktreePath: true)
        #expect(withWorktree.isBranchDiscoveryBlocked == true)

        let neither = ManualOverrides()
        #expect(neither.isBranchDiscoveryBlocked == false)
    }
}

// MARK: - KanbanCodeCard Tests

@Suite("KanbanCodeCard")
struct KanbanCodeCardTests {
    @Test func displayTitlePrefersLinkName() {
        let link = Link(name: "My Task")
        let card = KanbanCodeCard(link: link)
        #expect(card.displayTitle == "My Task")
    }

    @Test func displayTitleFallsToSession() {
        let link = Link()
        let session = Session(id: "s1", name: nil, firstPrompt: "Build me a thing", projectPath: nil, gitBranch: nil, messageCount: 1, modifiedTime: .now, jsonlPath: "/p")
        let card = KanbanCodeCard(link: link, session: session)
        #expect(card.displayTitle == "Build me a thing")
    }

    @Test func projectNameExtraction() {
        let link = Link(projectPath: "/Users/dev/my-app")
        let card = KanbanCodeCard(link: link)
        #expect(card.projectName == "my-app")
    }

    @Test func isActivelyWorking() {
        let working = KanbanCodeCard(link: Link(), activityState: .activelyWorking)
        #expect(working.isActivelyWorking == true)

        let idle = KanbanCodeCard(link: Link(), activityState: .idleWaiting)
        #expect(idle.isActivelyWorking == false)
    }

    @Test func showSpinner() {
        let active = KanbanCodeCard(link: Link(), activityState: .activelyWorking)
        #expect(active.showSpinner == true)

        var launchingLink = Link()
        launchingLink.isLaunching = true
        let launching = KanbanCodeCard(link: launchingLink)
        #expect(launching.showSpinner == true)

        let busy = KanbanCodeCard(link: Link(), isBusy: true)
        #expect(busy.showSpinner == true)

        let idle = KanbanCodeCard(link: Link())
        #expect(idle.showSpinner == false)
    }

    @Test func formatRelativeTime() {
        #expect(KanbanCodeCard.formatRelativeTime(.now) == "just now")
        #expect(KanbanCodeCard.formatRelativeTime(.now.addingTimeInterval(-120)) == "2m ago")
        #expect(KanbanCodeCard.formatRelativeTime(.now.addingTimeInterval(-7200)) == "2h ago")
        #expect(KanbanCodeCard.formatRelativeTime(.now.addingTimeInterval(-86400)) == "yesterday")
        #expect(KanbanCodeCard.formatRelativeTime(.now.addingTimeInterval(-86400 * 5)) == "5d ago")
        #expect(KanbanCodeCard.formatRelativeTime(.now.addingTimeInterval(-86400 * 60)) == "2mo ago")
    }

    @Test func columnDelegates() {
        let link = Link(column: .inReview)
        let card = KanbanCodeCard(link: link)
        #expect(card.column == .inReview)
    }
}

// MARK: - ActivityState Tests

@Suite("ActivityState")
struct ActivityStateTests {
    @Test func rawValueRoundTrip() {
        for state in [ActivityState.activelyWorking, .needsAttention, .idleWaiting, .ended, .stale] {
            #expect(ActivityState(rawValue: state.rawValue) == state)
        }
    }
}

// MARK: - CodingAssistant Tests

@Suite("CodingAssistant")
struct CodingAssistantTests {
    @Test func claudeDefaults() {
        #expect(CodingAssistant.claude.displayName == "Claude")
        #expect(CodingAssistant.claude.cliCommand == "claude")
        #expect(CodingAssistant.claude.supportsWorktree == true)
    }

    @Test func geminiDefaults() {
        #expect(CodingAssistant.gemini.displayName == "Gemini CLI")
        #expect(CodingAssistant.gemini.cliCommand == "gemini")
        #expect(CodingAssistant.gemini.supportsWorktree == false)
    }

    @Test func effectiveAssistantDefaultsToClaude() {
        let link = Link()
        #expect(link.effectiveAssistant == .claude)
    }
}

// MARK: - CheckRun Tests

@Suite("CheckRun")
struct CheckRunTests {
    @Test func equatable() {
        let a = CheckRun(name: "test", status: .completed, conclusion: .success)
        let b = CheckRun(name: "test", status: .completed, conclusion: .success)
        #expect(a == b)
    }

    @Test func statusRawValues() {
        #expect(CheckRunStatus(rawValue: "in_progress") == .inProgress)
        #expect(CheckRunConclusion(rawValue: "timed_out") == .timedOut)
        #expect(CheckRunConclusion(rawValue: "action_required") == .actionRequired)
    }
}
