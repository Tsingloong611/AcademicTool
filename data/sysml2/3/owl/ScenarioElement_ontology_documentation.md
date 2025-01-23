# Ontology Documentation

Generated on: 2025-01-23 21:06:01

## Classes

### 1

Super classes: AffectedElement

Properties: ClosureCondition, DesignSpeed, NumberOfLanes, RoadConstrucetionCondition, RoadMaintenanceConditon, RoadName, RoadType, SegmentEndStakeNumber, SegmentStartStakeNumber, SpeedLimit, TrafficCapacity, TrafficVolume, TravelTime


### 2

Super classes: EnvironmentElement

Properties: Rainfall, SnowfallIntensity, Visibility, WeatherType, WindForce, WindSpeed


### 3

Super classes: HazardElement

Properties: AbnormalSpeedCondition, BreakdownCondition, CollisionCondition, CombustionCondition, DrivingDirection, IIIegalLaneOccupationCondition, RollOverCondition, SpillCondition, VehiclePosition, VehicleSpeed, VehicleType, consistVehicleCargo, consistVehicleComponents, consistVehiclePassengers


### 32635536

Super classes: ResponsePlanElement

Properties: PlanName


### 32wqrw

Super classes: ResponsePlanElement


### 4

Super classes: AffectedElement

Properties: DamageCondition


### 44234

Super classes: ResponsePlanElement


### 5

Super classes: AffectedElement

Properties: PollutionCondition, RoadDamageCondition, consistIncludedFacilities, consistIncludedLanes


### 7

Super classes: ResponsePlanElement

Properties: ResourceQuantityOrQuality, ResourceType, ResourceUsageCondition


### 8

Super classes: ResponsePlanElement

Properties: BehaviorType, Duration, ImplementationCondition


### AffectedElement

Super classes: ScenarioElement


### AffectedStates

Super classes: ElementState


### CollideState

Super classes: HazardStates

Properties: SpillTransform


### CollidedState

Super classes: AffectedStates

Properties: ExplodeTransform


### DriveState

Super classes: HazardStates

Properties: CollideTransform


### DrivingState

Super classes: AffectedStates


### ElementCompositions

Super classes: Thing


### ElementState

Super classes: Thing


### EnvironmentElement

Super classes: ScenarioElement


### ExplodeState

Super classes: AffectedStates


### HazardElement

Super classes: ScenarioElement


### HazardStates

Super classes: ElementState


### IncludedFacilities

Super classes: ElementCompositions


### IncludedLanes

Super classes: ElementCompositions


### ResponseAction

Super classes: ResponsePlanElement


### ResponsePlanElement

Super classes: ScenarioElement


### ResponseResource

Super classes: ResponsePlanElement


### ResponseStates

Super classes: ElementState


### ScenarioElement

Super classes: Thing


### SpillState

Super classes: HazardStates


### VehicleCargo

Super classes: ElementCompositions


### VehicleComponents

Super classes: ElementCompositions


### VehiclePassengers

Super classes: ElementCompositions


### aidStates

Super classes: Thing


### ewa2

Super classes: ResponsePlanElement


### firefightingStates

Super classes: Thing


### idleState

Super classes: aidStates

Properties: Aid:ActionTransform, FireFighting:ActionTransform, Rescue:ActionTransform, Tow:ActionTransform


### implementState

Super classes: aidStates


### rescueStates

Super classes: Thing


### towStates

Super classes: Thing


### 人员

Super classes: ResponsePlanElement


### 你好

Super classes: ResponsePlanElement


### 抢修

Super classes: ResponsePlanElement


### 救助

Super classes: ResponsePlanElement


### 消防

Super classes: ResponsePlanElement


### 牵引

Super classes: ResponsePlanElement


### 那个

Super classes: ResponsePlanElement


### 预案1

Super classes: ResponsePlanElement


### 预案2

Super classes: ResponsePlanElement


### 预案3

Super classes: ResponsePlanElement


### 预案4

Super classes: ResponsePlanElement


### 预案5

Super classes: ResponsePlanElement


### 预案6

Super classes: ResponsePlanElement


## Properties

### Properties of 1

#### ClosureCondition

Type: DatatypeProperty

Range: <class 'int'>


#### DesignSpeed

Type: DatatypeProperty

Range: <class 'int'>


#### NumberOfLanes

Type: DatatypeProperty

Range: <class 'int'>


#### RoadConstrucetionCondition

Type: DatatypeProperty

Range: <class 'int'>


#### RoadMaintenanceConditon

Type: DatatypeProperty

Range: <class 'int'>


#### RoadName

Type: DatatypeProperty

Range: <class 'int'>


#### RoadType

Type: DatatypeProperty

Range: <class 'int'>


#### SegmentEndStakeNumber

Type: DatatypeProperty

Range: <class 'int'>


#### SegmentStartStakeNumber

Type: DatatypeProperty

Range: <class 'int'>


#### SpeedLimit

Type: DatatypeProperty

Range: <class 'int'>


#### TrafficCapacity

Type: DatatypeProperty

Range: <class 'int'>


#### TrafficVolume

Type: DatatypeProperty

Range: <class 'int'>


#### TravelTime

Type: DatatypeProperty

Range: <class 'int'>


### Properties of 2

#### Rainfall

Type: DatatypeProperty

Range: <class 'int'>


#### SnowfallIntensity

Type: DatatypeProperty

Range: <class 'int'>


#### Visibility

Type: DatatypeProperty

Range: <class 'int'>


#### WeatherType

Type: DatatypeProperty

Range: <class 'int'>


#### WindForce

Type: DatatypeProperty

Range: <class 'int'>


#### WindSpeed

Type: DatatypeProperty

Range: <class 'int'>


### Properties of 3

#### AbnormalSpeedCondition

Type: DatatypeProperty

Range: <class 'int'>


#### BreakdownCondition

Type: DatatypeProperty

Range: <class 'int'>


#### CollisionCondition

Type: DatatypeProperty

Range: <class 'int'>


#### CombustionCondition

Type: DatatypeProperty

Range: <class 'int'>


#### DrivingDirection

Type: DatatypeProperty

Range: <class 'int'>


#### IIIegalLaneOccupationCondition

Type: DatatypeProperty

Range: <class 'int'>


#### RollOverCondition

Type: DatatypeProperty

Range: <class 'int'>


#### SpillCondition

Type: DatatypeProperty

Range: <class 'int'>


#### VehiclePosition

Type: DatatypeProperty

Range: <class 'int'>


#### VehicleSpeed

Type: DatatypeProperty

Range: <class 'int'>


#### VehicleType

Type: DatatypeProperty

Range: <class 'int'>


#### consistVehicleCargo

Type: ObjectProperty

Range: VehicleCargo


#### consistVehicleComponents

Type: ObjectProperty

Range: VehicleComponents


#### consistVehiclePassengers

Type: ObjectProperty

Range: VehiclePassengers


### Properties of 32635536

#### PlanName

Type: DatatypeProperty

Range: <class 'int'>


### Properties of 4

#### DamageCondition

Type: DatatypeProperty

Range: <class 'int'>


### Properties of 5

#### PollutionCondition

Type: DatatypeProperty

Range: <class 'int'>


#### RoadDamageCondition

Type: DatatypeProperty

Range: <class 'int'>


#### consistIncludedFacilities

Type: ObjectProperty

Range: IncludedFacilities


#### consistIncludedLanes

Type: ObjectProperty

Range: IncludedLanes


### Properties of 7

#### ResourceQuantityOrQuality

Type: DatatypeProperty

Range: <class 'int'>


#### ResourceType

Type: DatatypeProperty

Range: <class 'int'>


#### ResourceUsageCondition

Type: DatatypeProperty

Range: <class 'int'>


### Properties of 8

#### BehaviorType

Type: DatatypeProperty

Range: <class 'int'>


#### Duration

Type: DatatypeProperty

Range: <class 'int'>


#### ImplementationCondition

Type: DatatypeProperty

Range: <class 'int'>


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


## Behaviors

## Rules

