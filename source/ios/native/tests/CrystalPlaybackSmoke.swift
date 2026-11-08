import Foundation

@main struct CrystalPlaybackSmoke {
    static func main() {
        var clock = CrystalClock()
        precondition(clock.state == .inspection)
        clock.play(); precondition(clock.time == 0 && clock.state == .playing)
        precondition(!clock.advance(0.4)); precondition(CrystalPose.sample(clock.time).stage == "Arrival")
        clock.pause(); let paused = clock.time; precondition(!clock.advance(10) && clock.time == paused)
        clock.play(); clock.speed = 2; precondition(!clock.advance(0.5)); precondition(abs(clock.time-1.4)<1e-9)
        clock.seek(2.9); precondition(clock.state == .paused && CrystalPose.sample(clock.time).opening > 0)
        clock.play(); precondition(clock.advance(10)); precondition(clock.state == .finished)
        precondition(!clock.advance(1))
        clock.restart(); precondition(clock.time == 0)
        clock.stop(); precondition(clock.state == .stopped && !clock.advance(1))
        clock.inspect(); precondition(clock.time == 1.6)
        for value in [Double.nan,Double.infinity,-Double.infinity,-10,0,0.9,2.55,3.75,4.15,100] {
            let pose = CrystalPose.sample(value)
            precondition([pose.scale,pose.opacity,pose.lift,pose.turn,pose.opening,pose.flash].allSatisfy(\.isFinite))
            precondition(pose.opacity >= 0 && pose.opacity <= 1 && pose.opening >= 0 && pose.opening <= 1)
        }
        precondition(CrystalPose.sample(4.15).stage == "Reveal ready")
        print("Crystal clock passed: stages, pause, restart, cancellation state, speed, invalid times and one-shot completion")
    }
}
