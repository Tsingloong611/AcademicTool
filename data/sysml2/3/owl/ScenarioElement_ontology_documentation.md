# Ontology Documentation

Generated on: 2025-02-07 15:37:29

## Classes

### 123445

Super classes: ResponsePlanElement

Properties: PlanName, associate123445-物资

Instances:

- **123445_inst**

  - PlanName: ['123445']
  - associate123445-物资: ['123445-物资_inst']


### 123445-救助

Super classes: ResponseAction

Instances:

- **123445-救助_inst**



### 123445-物资

Super classes: ResponseResource

Properties: associate123445-救助

Instances:

- **123445-物资_inst**

  - associate123445-救助: ['123445-救助_inst']


### 3256

Super classes: ResponsePlanElement

Properties: associate3256-人员, associate3256-物资

Instances:

- **3256_inst**

  - associate3256-人员: ['3256-人员_inst']
  - associate3256-物资: ['3256-物资_inst']


### 3256-人员

Super classes: ResponseResource

Properties: associate3256-牵引

Instances:

- **3256-人员_inst**

  - associate3256-牵引: ['3256-牵引_inst']


### 3256-救助

Super classes: ResponseAction

Instances:

- **3256-救助_inst**



### 3256-物资

Super classes: ResponseResource

Properties: associate3256-救助

Instances:

- **3256-物资_inst**

  - associate3256-救助: ['3256-救助_inst']


### 3256-牵引

Super classes: ResponseAction

Instances:

- **3256-牵引_inst**



### 5235

Super classes: HazardElement

Properties: EmergencyPeriod

Instances:

- **5235_inst**

  - EmergencyPeriod: ['上午']


### 674675

Super classes: ResponsePlanElement

Properties: associate674675-人员, associate674675-医生, associate674675-牵引, associate674675-类型B

Instances:

- **674675_inst**

  - associate674675-类型B: ['674675-类型B_inst']
  - associate674675-牵引: ['674675-牵引_inst']
  - associate674675-医生: ['674675-医生_inst']
  - associate674675-人员: ['674675-人员_inst']


### 674675-人员

Super classes: ResponseResource

Properties: associate674675-抢修

Instances:

- **674675-人员_inst**

  - associate674675-抢修: ['674675-抢修_inst']


### 674675-医生

Super classes: ResponseResource

Instances:

- **674675-医生_inst**



### 674675-抢修

Super classes: ResponseAction

Instances:

- **674675-抢修_inst**



### 674675-救助

Super classes: ResponseAction

Properties: BehaviorType, Duration, ImplementationCondition

Instances:

- **674675-救助_inst**

  - Duration: ['3.0']
  - ImplementationCondition: ['True']
  - BehaviorType: ['救助']


### 674675-牵引

Super classes: ResponseAction

Instances:

- **674675-牵引_inst**



### 674675-类型B

Super classes: ResponseResource

Properties: Location, ResourceQuantityOrQuality, ResourceType, ResourceUsageCondition, associate674675-救助

Instances:

- **674675-类型B_inst**

  - ResourceType: ['类型A']
  - ResourceQuantityOrQuality: ['1.0']
  - Location: ['123']
  - ResourceUsageCondition: ['False']
  - associate674675-救助: ['674675-救助_inst']


### Action

Super classes: Thing

Instances:

- **Action_inst**



### AffectedElement

Super classes: ScenarioElement

Instances:

- **AffectedElement_inst**


- **Road_inst**

  - DamageConditon: ['False']
  - RoadType: ['主路']
  - PollutionCondition: ['False']
  - ClosureCondition: ['False']

- **HazardVehicle_inst**

  - DamageCondition: ['False']
  - consistpassenger: ['People_inst']
  - VehiclePosition: ['ND569']
  - SpillCondition: ['True']
  - CollisionCondition: ['True']
  - associateRoad: ['Road_inst']
  - DrivingDirection: ['forward']
  - CombustionCondition: ['False']
  - VehicleType: ['truck']


### AffectedStates

Super classes: ElementState

Instances:

- **AffectedStates_inst**


- **ExplodeState_inst**


- **DrivingState_inst**


- **CollidedState_inst**



### Collide

Super classes: Thing

Instances:

- **Collide_inst**



### CollideState

Super classes: HazardStates

Properties: SpillTransform

Instances:

- **CollideState_inst**



### CollidedState

Super classes: AffectedStates

Properties: ExplodeTransform

Instances:

- **CollidedState_inst**



### DriveState

Super classes: HazardStates

Properties: CollideTransform

Instances:

- **DriveState_inst**



### DrivingState

Super classes: AffectedStates

Instances:

- **DrivingState_inst**



### ElementCompositions

Super classes: Thing

Instances:

- **VehicleLoad_inst**


- **Lane_inst**


- **VehiclePart_inst**


- **People_inst**


- **Facility_inst**



### ElementState

Super classes: Thing

Instances:

- **AffectedStates_inst**


- **HazardStates_inst**


- **ExplodeState_inst**


- **DrivingState_inst**


- **CollidedState_inst**


- **DriveState_inst**


- **CollideState_inst**


- **SpillState_inst**


- **rescueStates_inst**


- **idleState_inst**


- **implementState_inst**


- **towStates_inst**


- **firefightingStates_inst**


- **aidStates_inst**



### EnvironmentElement

Super classes: ScenarioElement

Instances:

- **EnvironmentElement_inst**


- **气象_inst**

  - SnowfallIntensity: ['']
  - WeatherType: ['晴天']


### Explode

Super classes: Thing

Instances:

- **Explode_inst**



### ExplodeState

Super classes: AffectedStates

Instances:

- **ExplodeState_inst**



### Facility

Super classes: ElementCompositions

Instances:

- **Facility_inst**



### Firefighting

Super classes: Thing

Instances:

- **Firefighting_inst**



### HazardElement

Super classes: ScenarioElement

Instances:

- **HazardElement_inst**


- **车辆_inst**

  - BreakdownCondition: ['False']
  - SpillCondition: ['False']
  - CollisionCondition: ['False']
  - IIIegalLaneOccupationCondition: ['False']
  - DrivingDirection: ['正向']
  - CombustionCondition: ['False']
  - RollOverCondition: ['False']

- **5235_inst**

  - EmergencyPeriod: ['上午']


### HazardStates

Super classes: ElementState

Instances:

- **HazardStates_inst**


- **DriveState_inst**


- **CollideState_inst**


- **SpillState_inst**



### HazardVehicle

Super classes: AffectedElement

Properties: DamageCondition, associateRoad, consistpassenger

Instances:

- **HazardVehicle_inst**

  - DamageCondition: ['False']
  - consistpassenger: ['People_inst']
  - VehiclePosition: ['ND569']
  - SpillCondition: ['True']
  - CollisionCondition: ['True']
  - associateRoad: ['Road_inst']
  - DrivingDirection: ['forward']
  - CombustionCondition: ['False']
  - VehicleType: ['truck']


### Lane

Super classes: ElementCompositions

Instances:

- **Lane_inst**



### People

Super classes: ElementCompositions

Instances:

- **People_inst**



### PersonnalRescue

Super classes: Thing

Instances:

- **PersonnalRescue_inst**



### ResponseAction

Super classes: ResponsePlanElement

Instances:

- **ResponseAction_inst**


- **674675-救助_inst**

  - Duration: ['3.0']
  - ImplementationCondition: ['True']
  - BehaviorType: ['救助']

- **674675-抢修_inst**


- **674675-牵引_inst**


- **3256-牵引_inst**


- **应急行为_inst**


- **123445-救助_inst**


- **3256-救助_inst**



### ResponsePlanElement

Super classes: ScenarioElement

Instances:

- **ResponsePlanElement_inst**


- **ResponseResource_inst**


- **ResponseAction_inst**


- **674675-类型B_inst**

  - ResourceType: ['类型A']
  - ResourceQuantityOrQuality: ['1.0']
  - Location: ['123']
  - ResourceUsageCondition: ['False']
  - associate674675-救助: ['674675-救助_inst']

- **674675-救助_inst**

  - Duration: ['3.0']
  - ImplementationCondition: ['True']
  - BehaviorType: ['救助']

- **674675-人员_inst**

  - associate674675-抢修: ['674675-抢修_inst']

- **674675-抢修_inst**


- **3256-人员_inst**

  - associate3256-牵引: ['3256-牵引_inst']

- **123445-物资_inst**

  - associate123445-救助: ['123445-救助_inst']

- **674675-牵引_inst**


- **3256-物资_inst**

  - associate3256-救助: ['3256-救助_inst']

- **123445_inst**

  - PlanName: ['123445']
  - associate123445-物资: ['123445-物资_inst']

- **3256_inst**

  - associate3256-人员: ['3256-人员_inst']
  - associate3256-物资: ['3256-物资_inst']

- **3256-牵引_inst**


- **应急行为_inst**


- **123445-救助_inst**


- **3256-救助_inst**


- **674675_inst**

  - associate674675-类型B: ['674675-类型B_inst']
  - associate674675-牵引: ['674675-牵引_inst']
  - associate674675-医生: ['674675-医生_inst']
  - associate674675-人员: ['674675-人员_inst']

- **674675-医生_inst**


- **应急资源_inst**



### ResponseResource

Super classes: ResponsePlanElement

Instances:

- **ResponseResource_inst**


- **674675-类型B_inst**

  - ResourceType: ['类型A']
  - ResourceQuantityOrQuality: ['1.0']
  - Location: ['123']
  - ResourceUsageCondition: ['False']
  - associate674675-救助: ['674675-救助_inst']

- **674675-人员_inst**

  - associate674675-抢修: ['674675-抢修_inst']

- **3256-人员_inst**

  - associate3256-牵引: ['3256-牵引_inst']

- **123445-物资_inst**

  - associate123445-救助: ['123445-救助_inst']

- **3256-物资_inst**

  - associate3256-救助: ['3256-救助_inst']

- **674675-医生_inst**


- **应急资源_inst**



### ResponseStates

Super classes: ElementState


### Road

Super classes: AffectedElement

Properties: ClosureCondition, DamageConditon, DesignSpeed, NumberOfLanes, PollutionCondition, RoadName, RoadType, SegmentEndStakeNumber, SegmentStartStakeNumber, TrafficVolume

Instances:

- **Road_inst**

  - DamageConditon: ['False']
  - RoadType: ['主路']
  - PollutionCondition: ['False']
  - ClosureCondition: ['False']


### RoadCleaning

Super classes: Thing

Instances:

- **RoadCleaning_inst**



### RoadControl

Super classes: Thing

Instances:

- **RoadControl_inst**



### RoadRepair

Super classes: Thing

Instances:

- **RoadRepair_inst**



### ScenarioElement

Super classes: Thing

Instances:

- **AffectedElement_inst**


- **HazardElement_inst**


- **EnvironmentElement_inst**


- **ResponsePlanElement_inst**


- **ResponseResource_inst**


- **ResponseAction_inst**


- **Road_inst**

  - DamageConditon: ['False']
  - RoadType: ['主路']
  - PollutionCondition: ['False']
  - ClosureCondition: ['False']

- **HazardVehicle_inst**

  - DamageCondition: ['False']
  - consistpassenger: ['People_inst']
  - VehiclePosition: ['ND569']
  - SpillCondition: ['True']
  - CollisionCondition: ['True']
  - associateRoad: ['Road_inst']
  - DrivingDirection: ['forward']
  - CombustionCondition: ['False']
  - VehicleType: ['truck']

- **气象_inst**

  - SnowfallIntensity: ['']
  - WeatherType: ['晴天']

- **车辆_inst**

  - BreakdownCondition: ['False']
  - SpillCondition: ['False']
  - CollisionCondition: ['False']
  - IIIegalLaneOccupationCondition: ['False']
  - DrivingDirection: ['正向']
  - CombustionCondition: ['False']
  - RollOverCondition: ['False']

- **5235_inst**

  - EmergencyPeriod: ['上午']

- **674675-类型B_inst**

  - ResourceType: ['类型A']
  - ResourceQuantityOrQuality: ['1.0']
  - Location: ['123']
  - ResourceUsageCondition: ['False']
  - associate674675-救助: ['674675-救助_inst']

- **674675-救助_inst**

  - Duration: ['3.0']
  - ImplementationCondition: ['True']
  - BehaviorType: ['救助']

- **674675-人员_inst**

  - associate674675-抢修: ['674675-抢修_inst']

- **674675-抢修_inst**


- **3256-人员_inst**

  - associate3256-牵引: ['3256-牵引_inst']

- **123445-物资_inst**

  - associate123445-救助: ['123445-救助_inst']

- **674675-牵引_inst**


- **3256-物资_inst**

  - associate3256-救助: ['3256-救助_inst']

- **123445_inst**

  - PlanName: ['123445']
  - associate123445-物资: ['123445-物资_inst']

- **3256_inst**

  - associate3256-人员: ['3256-人员_inst']
  - associate3256-物资: ['3256-物资_inst']

- **3256-牵引_inst**


- **应急行为_inst**


- **123445-救助_inst**


- **3256-救助_inst**


- **674675_inst**

  - associate674675-类型B: ['674675-类型B_inst']
  - associate674675-牵引: ['674675-牵引_inst']
  - associate674675-医生: ['674675-医生_inst']
  - associate674675-人员: ['674675-人员_inst']

- **674675-医生_inst**


- **应急资源_inst**



### Spill

Super classes: Thing

Instances:

- **Spill_inst**



### SpillState

Super classes: HazardStates

Instances:

- **SpillState_inst**



### VehicleBreakdown

Super classes: Thing

Instances:

- **VehicleBreakdown_inst**



### VehicleCollision

Super classes: Thing

Instances:

- **VehicleCollision_inst**



### VehicleDeparture

Super classes: Thing

Instances:

- **VehicleDeparture_inst**



### VehicleExplosion

Super classes: Thing

Instances:

- **VehicleExplosion_inst**



### VehicleLaneChange

Super classes: Thing

Instances:

- **VehicleLaneChange_inst**



### VehicleLoad

Super classes: ElementCompositions

Instances:

- **VehicleLoad_inst**



### VehicleMotion

Super classes: Thing

Instances:

- **VehicleMotion_inst**



### VehicleOverturn

Super classes: Thing

Instances:

- **VehicleOverturn_inst**



### VehiclePart

Super classes: ElementCompositions

Instances:

- **VehiclePart_inst**



### VehicleSpeedChange

Super classes: Thing

Instances:

- **VehicleSpeedChange_inst**



### VehicleSpillage

Super classes: Thing

Instances:

- **VehicleSpillage_inst**



### VehicleTowing

Super classes: Thing

Instances:

- **VehicleTowing_inst**



### VehicleTransport

Super classes: Thing

Instances:

- **VehicleTransport_inst**



### VehicleTurning

Super classes: Thing

Instances:

- **VehicleTurning_inst**



### aidStates

Super classes: ElementState

Instances:

- **aidStates_inst**



### firefightingStates

Super classes: ElementState

Instances:

- **firefightingStates_inst**



### idleState

Super classes: rescueStates

Properties: Aid:ActionTransform, FireFighting:ActionTransform, Rescue:ActionTransform, Tow:ActionTransform

Instances:

- **idleState_inst**



### implementState

Super classes: rescueStates

Instances:

- **implementState_inst**



### rescueStates

Super classes: ElementState

Instances:

- **rescueStates_inst**


- **idleState_inst**


- **implementState_inst**



### towStates

Super classes: ElementState

Instances:

- **towStates_inst**



### 应急行为

Super classes: ResponseAction

Instances:

- **应急行为_inst**



### 应急资源

Super classes: ResponseResource

Instances:

- **应急资源_inst**



### 气象

Super classes: EnvironmentElement

Properties: Rainfall, SnowfallIntensity, Visibility, WeatherType, WindForce, WindSpeed

Instances:

- **气象_inst**

  - SnowfallIntensity: ['']
  - WeatherType: ['晴天']


### 车辆

Super classes: HazardElement

Properties: AbnormalSpeedCondition, BreakdownCondition, CollisionCondition, CombustionCondition, DrivingDirection, IIIegalLaneOccupationCondition, RollOverCondition, SpillCondition, VehiclePosition, VehicleSpeed, VehicleType

Instances:

- **车辆_inst**

  - BreakdownCondition: ['False']
  - SpillCondition: ['False']
  - CollisionCondition: ['False']
  - IIIegalLaneOccupationCondition: ['False']
  - DrivingDirection: ['正向']
  - CombustionCondition: ['False']
  - RollOverCondition: ['False']


## Properties

### Properties of 123445

#### PlanName

Type: DatatypeProperty

Range: <class 'str'>


#### associate123445-物资

Type: ObjectProperty

Range: 123445-物资


### Properties of 123445-物资

#### associate123445-救助

Type: ObjectProperty

Range: 123445-救助


### Properties of 3256

#### associate3256-人员

Type: ObjectProperty

Range: 3256-人员


#### associate3256-物资

Type: ObjectProperty

Range: 3256-物资


### Properties of 3256-人员

#### associate3256-牵引

Type: ObjectProperty

Range: 3256-牵引


### Properties of 3256-物资

#### associate3256-救助

Type: ObjectProperty

Range: 3256-救助


### Properties of 5235

#### EmergencyPeriod

Type: DatatypeProperty

Range: <class 'str'>


### Properties of 674675

#### associate674675-人员

Type: ObjectProperty

Range: 674675-人员


#### associate674675-医生

Type: ObjectProperty

Range: 674675-医生


#### associate674675-牵引

Type: ObjectProperty

Range: 674675-牵引


#### associate674675-类型B

Type: ObjectProperty

Range: 674675-类型B


### Properties of 674675-人员

#### associate674675-抢修

Type: ObjectProperty

Range: 674675-抢修


### Properties of 674675-救助

#### BehaviorType

Type: DatatypeProperty

Range: <class 'str'>


#### Duration

Type: DatatypeProperty

Range: <class 'float'>


#### ImplementationCondition

Type: DatatypeProperty

Range: <class 'bool'>


### Properties of 674675-类型B

#### Location

Type: DatatypeProperty

Range: <class 'str'>


#### ResourceQuantityOrQuality

Type: DatatypeProperty

Range: <class 'float'>


#### ResourceType

Type: DatatypeProperty

Range: <class 'str'>


#### ResourceUsageCondition

Type: DatatypeProperty

Range: <class 'bool'>


#### associate674675-救助

Type: ObjectProperty

Range: 674675-救助


### Properties of CollideState

#### SpillTransform

Type: ObjectProperty

Range: SpillState


### Properties of CollidedState

#### ExplodeTransform

Type: ObjectProperty

Range: ExplodeState


### Properties of DriveState

#### CollideTransform

Type: ObjectProperty

Range: CollideState


### Properties of HazardVehicle

#### DamageCondition

Type: DatatypeProperty

Range: <class 'bool'>


#### associateRoad

Type: ObjectProperty

Range: Road


#### consistpassenger

Type: ObjectProperty

Range: People


### Properties of Road

#### ClosureCondition

Type: DatatypeProperty

Range: <class 'bool'>


#### DamageConditon

Type: DatatypeProperty

Range: <class 'bool'>


#### DesignSpeed

Type: DatatypeProperty

Range: <class 'float'>


#### NumberOfLanes

Type: DatatypeProperty

Range: <class 'float'>


#### PollutionCondition

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadName

Type: DatatypeProperty

Range: <class 'str'>


#### RoadType

Type: DatatypeProperty

Range: <class 'str'>


#### SegmentEndStakeNumber

Type: DatatypeProperty

Range: <class 'str'>


#### SegmentStartStakeNumber

Type: DatatypeProperty

Range: <class 'str'>


#### TrafficVolume

Type: DatatypeProperty

Range: <class 'float'>


### Properties of idleState

#### Aid:ActionTransform

Type: ObjectProperty

Range: implementState


#### FireFighting:ActionTransform

Type: ObjectProperty

Range: implementState


#### Rescue:ActionTransform

Type: ObjectProperty

Range: implementState


#### Tow:ActionTransform

Type: ObjectProperty

Range: implementState


### Properties of 气象

#### Rainfall

Type: DatatypeProperty

Range: <class 'float'>


#### SnowfallIntensity

Type: DatatypeProperty

Range: <class 'str'>


#### Visibility

Type: DatatypeProperty

Range: <class 'float'>


#### WeatherType

Type: DatatypeProperty

Range: <class 'str'>


#### WindForce

Type: DatatypeProperty

Range: <class 'float'>


#### WindSpeed

Type: DatatypeProperty

Range: <class 'float'>


### Properties of 车辆

#### AbnormalSpeedCondition

Type: DatatypeProperty

Range: <class 'str'>


#### BreakdownCondition

Type: DatatypeProperty

Range: <class 'bool'>


#### CollisionCondition

Type: DatatypeProperty

Range: <class 'bool'>


#### CombustionCondition

Type: DatatypeProperty

Range: <class 'bool'>


#### DrivingDirection

Type: DatatypeProperty

Range: <class 'str'>


#### IIIegalLaneOccupationCondition

Type: DatatypeProperty

Range: <class 'bool'>


#### RollOverCondition

Type: DatatypeProperty

Range: <class 'bool'>


#### SpillCondition

Type: DatatypeProperty

Range: <class 'bool'>


#### VehiclePosition

Type: DatatypeProperty

Range: <class 'str'>


#### VehicleSpeed

Type: DatatypeProperty

Range: <class 'float'>


#### VehicleType

Type: DatatypeProperty

Range: <class 'str'>


## Behaviors

## Rules

