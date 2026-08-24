// swift-tools-version:5.9
import PackageDescription

let package = Package(
    name: "VeriPayKit",
    platforms: [.iOS(.v15)],
    products: [.library(name: "VeriPayKit", targets: ["VeriPayKit"])],
    targets: [
        .target(name: "VeriPayKit", path: "Sources/VeriPayKit"),
        .testTarget(name: "VeriPayKitTests", dependencies: ["VeriPayKit"], path: "Tests"),
    ]
)
