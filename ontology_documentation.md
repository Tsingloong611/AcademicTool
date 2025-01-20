# Ontology Documentation

Generated on: 2025-01-19 23:55:27

## Classes

### 169

Super classes: Thing


### 3

Super classes: AffectedElement

Properties: DamageCondition


### 5

Super classes: EnvironmentElement

Properties: Rainfall, SnowfallIntensity, Visibility, WeatherType, WindForce, WindSpeed


### 6

Super classes: HazardElement

Properties: AbnormalSpeedCondition, BreakdownCondition, CollisionCondition, CombustionCondition, DrivingDirection, IIIegalLaneOccupationCondition, RollOverCondition, SpillCondition, VehiclePosition, VehicleSpeed, VehicleType, consistVehicleCargo, consistVehicleComponents, consistVehiclePassengers


### 7

Super classes: ResponsePlanElement

Properties: ResourceQuantityOrQuality, ResourceType, ResourceUsageCondition


### 8

Super classes: ResponsePlanElement

Properties: BehaviorType, Duration, ImplementationCondition


### AbsorptionScenario

Super classes: Scenario


### AdaptionScenario

Super classes: Scenario


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


### EconomicFactors

Super classes: ResilienceInfluentialFactors

Properties: actionType, resourceType, roadLoss


### ElementCompositions

Super classes: Thing


### ElementState

Super classes: Thing


### Emergency

Super classes: Thing

Properties: inPhase, involvesScenario


### EmergencyPhase

Super classes: Thing


### EnvironmentElement

Super classes: ScenarioElement


### ExplodeState

Super classes: AffectedStates


### FunctionFactors

Super classes: ResilienceInfluentialFactors

Properties: roadPassibility


### HazardElement

Super classes: ScenarioElement


### HazardStates

Super classes: ElementState


### HazardVehicle

Super classes: AffectedElement


### IncludedFacilities

Super classes: ElementCompositions


### IncludedLanes

Super classes: ElementCompositions


### InvolvedScenario

Super classes: Thing


### InvolvedScenarioElement

Super classes: Thing


### RecoveryScenario

Super classes: Scenario


### ResilienceInfluentialFactors

Super classes: Thing


### ResponseAction

Super classes: ResponsePlanElement


### ResponsePlanElement

Super classes: ScenarioElement


### ResponseResource

Super classes: ResponsePlanElement


### Road

Super classes: AffectedElement

Properties: ClosureCondition, DamageConditon, DesignSpeed, NumberOfLanes, PollutionCondition, RoadName, RoadType, SegmentEndStakeNumber, SegmentStartStakeNumber, TrafficVolume, consistIncludedFacilities, consistIncludedLanes


### SafetyFactors

Super classes: ResilienceInfluentialFactors

Properties: casualties, emergencyType


### Scenario

Super classes: Thing

Properties: hasResilience, influencedBy, involvesElement


### ScenarioElement

Super classes: Thing


### ScenarioResilience

Super classes: Thing


### SpillState

Super classes: HazardStates


### TimeFactors

Super classes: ResilienceInfluentialFactors

Properties: disposalDuration, emergencyPeriod, responseDuration


### VehicleCargo

Super classes: ElementCompositions


### VehicleComponents

Super classes: ElementCompositions


### VehiclePassengers

Super classes: ElementCompositions


### aidStates

Super classes: Thing


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


## Properties

### Properties of 3

#### DamageCondition

Type: DatatypeProperty

Range: <class 'float'>


### Properties of 5

#### Rainfall

Type: DatatypeProperty

Range: <class 'float'>


#### SnowfallIntensity

Type: DatatypeProperty

Range: <class 'float'>


#### Visibility

Type: DatatypeProperty

Range: <class 'float'>


#### WeatherType

Type: DatatypeProperty

Range: <class 'float'>


#### WindForce

Type: DatatypeProperty

Range: <class 'float'>


#### WindSpeed

Type: DatatypeProperty

Range: <class 'float'>


### Properties of 6

#### AbnormalSpeedCondition

Type: DatatypeProperty

Range: <class 'str'>


#### BreakdownCondition

Type: DatatypeProperty

Range: <class 'float'>


#### CollisionCondition

Type: DatatypeProperty

Range: <class 'float'>


#### CombustionCondition

Type: DatatypeProperty

Range: <class 'float'>


#### DrivingDirection

Type: DatatypeProperty

Range: <class 'float'>


#### IIIegalLaneOccupationCondition

Type: DatatypeProperty

Range: <class 'float'>


#### RollOverCondition

Type: DatatypeProperty

Range: <class 'float'>


#### SpillCondition

Type: DatatypeProperty

Range: <class 'float'>


#### VehiclePosition

Type: DatatypeProperty

Range: <class 'str'>


#### VehicleSpeed

Type: DatatypeProperty

Range: <class 'float'>


#### VehicleType

Type: DatatypeProperty

Range: <class 'str'>


#### consistVehicleCargo

Type: ObjectProperty

Range: VehicleCargo


#### consistVehicleComponents

Type: ObjectProperty

Range: VehicleComponents


#### consistVehiclePassengers

Type: ObjectProperty

Range: VehiclePassengers


### Properties of 7

#### ResourceQuantityOrQuality

Type: DatatypeProperty

Range: <class 'float'>


#### ResourceType

Type: DatatypeProperty

Range: <class 'float'>


#### ResourceUsageCondition

Type: DatatypeProperty

Range: <class 'float'>


### Properties of 8

#### BehaviorType

Type: DatatypeProperty

Range: <class 'float'>


#### Duration

Type: DatatypeProperty

Range: <class 'float'>


#### ImplementationCondition

Type: DatatypeProperty

Range: <class 'float'>


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


### Properties of EconomicFactors

#### actionType

Type: DatatypeProperty

Range: <class 'str'>


#### resourceType

Type: DatatypeProperty

Range: <class 'str'>


#### roadLoss

Type: DatatypeProperty

Range: <class 'bool'>


### Properties of Emergency

#### inPhase

Type: ObjectProperty

Range: EmergencyPhase


#### involvesScenario

Type: ObjectProperty

Range: InvolvedScenario


### Properties of FunctionFactors

#### roadPassibility

Type: DatatypeProperty

Range: <class 'bool'>


### Properties of Road

#### ClosureCondition

Type: DatatypeProperty

Range: <class 'float'>


#### DamageConditon

Type: DatatypeProperty

Range: <class 'float'>


#### DesignSpeed

Type: DatatypeProperty

Range: <class 'float'>


#### NumberOfLanes

Type: DatatypeProperty

Range: <class 'float'>


#### PollutionCondition

Type: DatatypeProperty

Range: <class 'float'>


#### RoadName

Type: DatatypeProperty

Range: <class 'str'>


#### RoadType

Type: DatatypeProperty

Range: <class 'float'>


#### SegmentEndStakeNumber

Type: DatatypeProperty

Range: <class 'str'>


#### SegmentStartStakeNumber

Type: DatatypeProperty

Range: <class 'str'>


#### TrafficVolume

Type: DatatypeProperty

Range: <class 'float'>


#### consistIncludedFacilities

Type: ObjectProperty

Range: IncludedFacilities


#### consistIncludedLanes

Type: ObjectProperty

Range: IncludedLanes


### Properties of SafetyFactors

#### casualties

Type: DatatypeProperty

Range: <class 'bool'>


#### emergencyType

Type: DatatypeProperty

Range: <class 'str'>


### Properties of Scenario

#### hasResilience

Type: ObjectProperty

Range: ScenarioResilience


#### influencedBy

Type: ObjectProperty

Range: ResilienceInfluentialFactors


#### involvesElement

Type: ObjectProperty

Range: InvolvedScenarioElement


### Properties of TimeFactors

#### disposalDuration

Type: DatatypeProperty

Range: <class 'str'>


#### emergencyPeriod

Type: DatatypeProperty

Range: <class 'str'>


#### responseDuration

Type: DatatypeProperty

Range: <class 'str'>


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

