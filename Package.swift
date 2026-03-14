// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "KanbanCodeiPhone",
    platforms: [
        .iOS(.v17),
    ],
    products: [
        .library(name: "KanbanCodeCore", targets: ["KanbanCodeCore"]),
    ],
    dependencies: [
        .package(url: "https://github.com/gonzalezreal/swift-markdown-ui", from: "2.4.0"),
    ],
    targets: [
        .target(
            name: "KanbanCodeCore",
            path: "Sources/KanbanCodeCore"
        ),
        .executableTarget(
            name: "KanbanCodeiPhone",
            dependencies: [
                "KanbanCodeCore",
                .product(name: "MarkdownUI", package: "swift-markdown-ui"),
            ],
            path: "Sources/KanbanCodeiPhone",
            resources: [.copy("Resources")]
        ),
        .testTarget(
            name: "KanbanCodeCoreTests",
            dependencies: ["KanbanCodeCore"],
            path: "Tests/KanbanCodeCoreTests"
        ),
    ]
)
