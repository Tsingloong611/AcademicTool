# Ontology Documentation

Generated on: 2025-01-23 17:23:47

## Classes

### 345

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


### HazardVehicle

Super classes: AffectedElement

Properties: DamageCondition


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


### Road

Super classes: AffectedElement

Properties: ClosureCondition, DesignSpeed, NumberOfLanes, PollutionCondition, RoadDamageCondition, RoadName, RoadType, SegmentEndStakeNumber, SegmentStartStakeNumber, TrafficVolume, consistIncludedFacilities, consistIncludedLanes


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


### affectedvehicle

Super classes: HazardElement

Properties: AbnormalSpeedCondition, BreakdownCondition, CollisionCondition, CombustionCondition, DrivingDirection, IIIegalLaneOccupationCondition, RollOverCondition, SpillCondition, VehiclePosition, VehicleSpeed, VehicleType, consistVehicleCargo, consistVehicleComponents, consistVehiclePassengers


### aidStates

Super classes: Thing


### emergencyaction1

Super classes: ResponsePlanElement


### emergencyresource1

Super classes: ResponsePlanElement

Properties: ResourceQuantityOrQuality, ResourceType, ResourceUsageCondition


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


### weather

Super classes: EnvironmentElement

Properties: Rainfall, SnowfallIntensity, Visibility, WeatherType, WindForce, WindSpeed


### 人员

Super classes: ResponsePlanElement


### 我

Super classes: ResponsePlanElement

Properties: PlanName


### 救助

Super classes: ResponsePlanElement


## Properties

### Properties of 345

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


### Properties of HazardVehicle

#### DamageCondition

Type: DatatypeProperty

Range: <class 'int'>


### Properties of Road

#### ClosureCondition

Type: DatatypeProperty

Range: <class 'int'>


#### DesignSpeed

Type: DatatypeProperty

Range: <class 'int'>


#### NumberOfLanes

Type: DatatypeProperty

Range: <class 'int'>


#### PollutionCondition

Type: DatatypeProperty

Range: <class 'int'>


#### RoadDamageCondition

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


#### TrafficVolume

Type: DatatypeProperty

Range: <class 'int'>


#### consistIncludedFacilities

Type: ObjectProperty

Range: IncludedFacilities


#### consistIncludedLanes

Type: ObjectProperty

Range: IncludedLanes


### Properties of affectedvehicle

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


### Properties of emergencyresource1

#### ResourceQuantityOrQuality

Type: DatatypeProperty

Range: <class 'int'>


#### ResourceType

Type: DatatypeProperty

Range: <class 'int'>


#### ResourceUsageCondition

Type: DatatypeProperty

Range: <class 'int'>


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


### Properties of weather

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


### Properties of 我

#### PlanName

Type: DatatypeProperty

Range: <class 'int'>


## Behaviors

## Rules

