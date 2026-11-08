import Foundation
@main struct Check {
 static func main() {
  let p=ObtainedActionPolicy.originalStyle(masterID:"100005404")
  assert(p.sample(at:0,attackTicks:[60,60],idleTicks:[48]).kind=="idle")
  assert(p.sample(at:0.8,attackTicks:[60,60],idleTicks:[48]).kind=="atk")
  assert(p.sample(at:2.8,attackTicks:[60,60],idleTicks:[48]).kind=="idle")
  assert(p.sample(at:999,attackTicks:[60,60],idleTicks:[48]).kind=="idle")
  assert(p.sample(at:1,attackTicks:nil,idleTicks:[48]).kind=="idle")
  let c=ObtainedActionPolicy.originalStyle(masterID:"100004604")
  assert(c.sample(at:3.7,attackTicks:[60,60],idleTicks:[48]).kind=="atk")
  assert(c.sample(at:6,attackTicks:[60,60],idleTicks:[48]).kind=="idle")
  for width in [320.0,402.0,768.0] {
   let body=ObtainedBodyFraming.scale(width:width,height:360,sourceWidth:90,sourceHeight:120)
   assert(abs(body-2.16)<1e-9) // 120 source pixels occupy 72% of a 360-point stage.
  }
  assert(ObtainedBodyFraming.scale(width:.nan,height:360,sourceWidth:90,sourceHeight:120)==1)
  print("Finite obtained policy and fallback passed")
 }
}
