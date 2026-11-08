import Foundation

struct GlobalMenuMetrics {
    let width: Double
    var scale: Double { min(width,640)/640 }
    var tabHeight: Double { max(44,64*scale) }
    var bannerWidth: Double { min(width,640) }
}
