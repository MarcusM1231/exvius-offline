import Foundation

// Reconstructed camera-space paths. Counts/times are configurable here, not
// recovered BMB keyframes and never a representation of how many units are awarded.
enum CrystalEntranceTiming {
    static let fallingDuration = 3.2
    static let arrivalDuration = 0.9
    static let heroLead = 0.55
    static let fallingWidth = 1.25 // User reference: broader falling silhouettes; settled mesh stays unchanged.
    static let count = 8 // Seven passing crystals plus the one existing main crystal.
    static let totalArrival = fallingDuration+arrivalDuration
}
struct FallingCrystalPose {
    let x: Double, y: Double, z: Double, scale: Double, roll: Double, opacity: Double
    var visible: Bool { opacity > 0 }
    static func decorativeAppearance(index: Int) -> CrystalAppearance {
        let colors: [CrystalAppearance] = [.blue,.gold,.blue,.rainbow,.gold,.blue,.rainbow]
        return colors[max(0,min(colors.count-1,index))]
    }
    static func sample(index: Int,time: Double) -> FallingCrystalPose {
        let x = [-10.0,7.0,-4.0,12.0,-12.0,3.0,9.0]
        let size = [0.20,0.31,0.16,0.40,0.29,0.22,0.36]
        guard x.indices.contains(index), time.isFinite else { return FallingCrystalPose(x:0,y:0,z:0,scale:0,roll:0,opacity:0) }
        let start = -0.30+Double(index)*0.27
        let progress = (time-start)/1.7
        let alpha = max(0,min(1,min(progress/0.10,(1-progress)/0.14)))
        let ending = max(0,min(1,(CrystalEntranceTiming.fallingDuration-time)/0.35))
        return FallingCrystalPose(x:x[index]+sin(progress*2.1+Double(index))*0.8,
            y:28-57*progress,z:Double(index%4)*4-9,scale:size[index],
            roll:sin(time*1.2+Double(index))*0.14,opacity:alpha*ending)
    }
}
