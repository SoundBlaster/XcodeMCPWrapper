// swift-tools-version:5.9
// This is a minimal Package.swift for DocC documentation generation only.
// The actual mcpbridge-wrapper is a Python project.

import PackageDescription

let package = Package(
    name: "XcodeMCPWrapper",
    products: [
        .library(
            name: "XcodeMCPWrapper",
            targets: ["XcodeMCPWrapper"]
        ),
        .executable(
            name: "XcodeMCPWrapper-docs",
            targets: ["XcodeMCPWrapper-docs"]
        ),
    ],
    dependencies: [
        .package(url: "https://github.com/apple/swift-docc-plugin", from: "1.0.0"),
    ],
    targets: [
        .target(
            name: "XcodeMCPWrapper",
            path: "Sources/XcodeMCPWrapper",
            exclude: []
        ),
        .executableTarget(
            name: "XcodeMCPWrapper-docs",
            path: "Sources/XcodeMCPWrapper-docs",
            exclude: []
        ),
    ]
)
