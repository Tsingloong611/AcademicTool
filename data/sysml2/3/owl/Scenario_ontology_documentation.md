# Ontology Documentation

Generated on: 2025-02-21 21:07:30

## Classes

### AbsorptionScenario

Super classes: Scenario


### AdaptionScenario

Super classes: Scenario


### EconomicFactors

Super classes: ResilienceInfluentialFactors

Properties: resourceType, roadLoss


### FunctionFactors

Super classes: ResilienceInfluentialFactors

Properties: roadPassibility


### InvolvedScenarioElement

Super classes: Thing


### RecoveryScenario

Super classes: Scenario


### ResilienceInfluentialFactors

Super classes: Thing


### SafetyFactors

Super classes: ResilienceInfluentialFactors

Properties: casualties, emergencyType


### Scenario

Super classes: Thing

Properties: hasResilience, influencedBy, involvesElement


### ScenarioResilience

Super classes: Thing


### TimeFactors

Super classes: ResilienceInfluentialFactors

Properties: disposalDuration, emergencyPeriod, responseDuration


## Properties

### Properties of 14-救助

#### Firefighting

Type: ObjectProperty


#### PersonnalRescue

Type: ObjectProperty


#### RoadCleaning

Type: ObjectProperty


#### RoadControl

Type: ObjectProperty


#### RoadRepair

Type: ObjectProperty


#### VehicleTowing

Type: ObjectProperty


### Properties of AffectedVehicle

#### VehicleDeparture

Type: ObjectProperty


#### VehicleExplosion

Type: ObjectProperty


#### VehicleMotion

Type: ObjectProperty


#### VehicleSpeedChange

Type: ObjectProperty


#### VehicleSpillage

Type: ObjectProperty


#### VehicleTransport

Type: ObjectProperty


### Properties of EconomicFactors

#### resourceType

Type: DatatypeProperty

Range: <class 'str'>


#### roadLoss

Type: DatatypeProperty

Range: <class 'bool'>


### Properties of FunctionFactors

#### roadPassibility

Type: DatatypeProperty

Range: <class 'bool'>


### Properties of HazardVehicle

#### VehicleBreakdown

Type: ObjectProperty


#### VehicleCollision

Type: ObjectProperty

Range: Road


#### VehicleDeparture

Type: ObjectProperty


#### VehicleExplosion

Type: ObjectProperty


#### VehicleLaneChange

Type: ObjectProperty


#### VehicleMotion

Type: ObjectProperty


#### VehicleOverturn

Type: ObjectProperty

Range: Road


#### VehicleSpeedChange

Type: ObjectProperty


#### VehicleSpillage

Type: ObjectProperty


#### VehicleTransport

Type: ObjectProperty


#### VehicleTurning

Type: ObjectProperty


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


### Properties of plan1-救助

#### Firefighting

Type: ObjectProperty


#### PersonnalRescue

Type: ObjectProperty


#### RoadCleaning

Type: ObjectProperty


#### RoadControl

Type: ObjectProperty


#### RoadRepair

Type: ObjectProperty


#### VehicleTowing

Type: ObjectProperty


## Behaviors

## Rules

