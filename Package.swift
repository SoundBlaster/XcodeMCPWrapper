// swift-tools-version:5.9
// This is a minimal Package.swift for DocC documentation generation only.
// The actual mcpbridge-wrapper is a Python project.

import PackageDescription

let package = Package(
    name: "mcpbridge-wrapper",
    products: [
        .library(
            name: "mcpbridge-wrapper",
            targets: ["mcpbridge-wrapper"]
        ),
        .executable(
            name: "mcpbridge-wrapper-docs",
            targets: ["mcpbridge-wrapper-docs"]
        ),
    ],
    targets: [
        .target(
            name: "mcpbridge-wrapper",
            path: "Sources/mcpbridge-wrapper",
            exclude: []
        ),
        .executableTarget(
            name: "mcpbridge-wrapper-docs",
            path: "Sources/mcpbridge-wrapper-docs",
            exclude: []
        ),
    ]
)
