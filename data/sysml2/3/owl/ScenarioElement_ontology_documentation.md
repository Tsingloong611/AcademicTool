# Ontology Documentation

Generated on: 2025-02-21 21:07:30

## Classes

### AffectedElement

Super classes: ScenarioElement


### AffectedVehicle

Super classes: AffectedElement

Properties: CombustionCondition_AffectedVehicle, DamageCondition_AffectedVehicle, DrivingRoadSegment_AffectedVehicle, SpillCondition_AffectedVehicle, VehicleCargo_AffectedVehicle, VehicleComponents_AffectedVehicle, VehicleDeparture_AffectedVehicle, VehicleExplosion_AffectedVehicle, VehicleMotion_AffectedVehicle, VehiclePassengers_AffectedVehicle, VehicleSpeedChange_AffectedVehicle, VehicleSpeed_AffectedVehicle, VehicleSpillage_AffectedVehicle, VehicleTransport_AffectedVehicle, drivingDirection_AffectedVehicle, position_AffectedVehicle, vehicleType_AffectedVehicle


### Class_1

Super classes: Item

Properties: IsDetached_1, LoadedOn_1, VehicleLoadTyoe_1


### Class_14

Super classes: ResponsePlanElement

Properties: HasAction_14, HasResource_14, PlanName_14


### Class_14-医生

Super classes: ResponsePlanElement

Properties: AssociatedBehavior_14-医生, Location_14-医生, ResourceQuantityOrQuality_14-医生, ResourceType_14-医生, ResourceUsageCondition_14-医生


### Class_14-救助

Super classes: ResponsePlanElement

Properties: BehaviorType_14-救助, Duration_14-救助, EmergencyVehicles_14-救助, Firefighting_14-救助, ImplementationCondition_14-救助, ImplementingPersonnel_14-救助, InvolvedMaterials_14-救助, PersonnalRescue_14-救助, RoadCleaning_14-救助, RoadControl_14-救助, RoadRepair_14-救助, TargetOfImplementation_14-救助, VehicleTowing_14-救助


### Class_2

Super classes: Item

Properties: FacilityDamageStatus_2, FacilityLocation_2, FacilityType_2, RoadFacilityOf_2


### Class_23

Super classes: AffectedElement

Properties: ClosureCondition_23, DesignSpeed_23, IncludedFacilities_23, IncludedLanes_23, IncludedVehicles_23, NumberOfLanes_23, PollutionCondition_23, RoadConstrucetionCondition_23, RoadDamageCondition_23, RoadMaintenanceConditon_23, RoadName_23, RoadType_23, SegmentEndStakeNumber_23, SegmentStartStakeNumber_23, TrafficVolume_23


### EnvironmentElement

Super classes: ScenarioElement


### HazardElement

Super classes: ScenarioElement


### HazardVehicle

Super classes: HazardElement

Properties: AbnormalSpeedCondition_HazardVehicle, BreakdownCondition_HazardVehicle, CollideCondition_HazardVehicle, CombustionCondition_HazardVehicle, DrivingRoadSegment_HazardVehicle, EmergencyPeriod_HazardVehicle, IIIegalLaneOccupationCondition_HazardVehicle, RollOverCondition_HazardVehicle, SpillCondition_HazardVehicle, VehicleBreakdown_HazardVehicle, VehicleCargo_HazardVehicle, VehicleCollision_HazardVehicle, VehicleComponents_HazardVehicle, VehicleDeparture_HazardVehicle, VehicleExplosion_HazardVehicle, VehicleLaneChange_HazardVehicle, VehicleMotion_HazardVehicle, VehicleOverturn_HazardVehicle, VehiclePassengers_HazardVehicle, VehicleSpeedChange_HazardVehicle, VehicleSpeed_HazardVehicle, VehicleSpillage_HazardVehicle, VehicleTransport_HazardVehicle, VehicleTurning_HazardVehicle, drivingDirection_HazardVehicle, position_HazardVehicle, vehicleType_HazardVehicle


### Item

Super classes: Thing


### Meteorology

Super classes: EnvironmentElement

Properties: AffectedArea_Meteorology, Rainfall_Meteorology, SnowfallIntensity_Meteorology, Visibility_Meteorology, WeatherType_Meteorology, WindForce_Meteorology, WindSpeed_Meteorology


### ResponsePlanElement

Super classes: ScenarioElement


### Road

Super classes: EnvironmentElement

Properties: ClosureCondition_Road, DesignSpeed_Road, IncludedFacilities_Road, IncludedLanes_Road, IncludedVehicles_Road, NumberOfLanes_Road, PollutionCondition_Road, RoadConstrucetionCondition_Road, RoadDamageCondition_Road, RoadMaintenanceConditon_Road, RoadName_Road, RoadType_Road, SegmentEndStakeNumber_Road, SegmentStartStakeNumber_Road, SpeedLimit_Road, TrafficCapacity_Road, TrafficVolume_Road, TravelTime_Road


### ScenarioElement

Super classes: Thing


### hello

Super classes: AffectedElement

Properties: ClosureCondition_hello, DesignSpeed_hello, IncludedFacilities_hello, IncludedLanes_hello, IncludedVehicles_hello, NumberOfLanes_hello, PollutionCondition_hello, RoadConstrucetionCondition_hello, RoadDamageCondition_hello, RoadMaintenanceConditon_hello, RoadName_hello, RoadType_hello, SegmentEndStakeNumber_hello, SegmentStartStakeNumber_hello, TrafficVolume_hello


### hoa

Super classes: EnvironmentElement

Properties: ClosureCondition_hoa, DesignSpeed_hoa, IncludedFacilities_hoa, IncludedLanes_hoa, IncludedVehicles_hoa, NumberOfLanes_hoa, PollutionCondition_hoa, RoadConstrucetionCondition_hoa, RoadDamageCondition_hoa, RoadMaintenanceConditon_hoa, RoadName_hoa, RoadType_hoa, SegmentEndStakeNumber_hoa, SegmentStartStakeNumber_hoa, SpeedLimit_hoa, TrafficCapacity_hoa, TrafficVolume_hoa, TravelTime_hoa


### hob

Super classes: AffectedElement

Properties: ClosureCondition_hob, DesignSpeed_hob, IncludedFacilities_hob, IncludedLanes_hob, IncludedVehicles_hob, NumberOfLanes_hob, PollutionCondition_hob, RoadConstrucetionCondition_hob, RoadDamageCondition_hob, RoadMaintenanceConditon_hob, RoadName_hob, RoadType_hob, SegmentEndStakeNumber_hob, SegmentStartStakeNumber_hob, TrafficVolume_hob


### passenger

Super classes: Item

Properties: AffiliatedVehicle_passenger, CasualtyCondition_passenger


### plan1

Super classes: ResponsePlanElement

Properties: HasAction_plan1, HasResource_plan1, PlanName_plan1


### plan1-人员

Super classes: ResponsePlanElement

Properties: AssociatedBehavior_plan1-人员, Location_plan1-人员, ResourceQuantityOrQuality_plan1-人员, ResourceType_plan1-人员, ResourceUsageCondition_plan1-人员


### plan1-救助

Super classes: ResponsePlanElement

Properties: BehaviorType_plan1-救助, Duration_plan1-救助, EmergencyVehicles_plan1-救助, Firefighting_plan1-救助, ImplementationCondition_plan1-救助, ImplementingPersonnel_plan1-救助, InvolvedMaterials_plan1-救助, PersonnalRescue_plan1-救助, RoadCleaning_plan1-救助, RoadControl_plan1-救助, RoadRepair_plan1-救助, TargetOfImplementation_plan1-救助, VehicleTowing_plan1-救助


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

#### CombustionCondition_AffectedVehicle

Type: DatatypeProperty

Range: <class 'bool'>


#### DamageCondition_AffectedVehicle

Type: DatatypeProperty

Range: <class 'bool'>


#### DrivingRoadSegment_AffectedVehicle

Type: ObjectProperty

Range: Road


#### SpillCondition_AffectedVehicle

Type: DatatypeProperty

Range: <class 'bool'>


#### VehicleCargo_AffectedVehicle

Type: ObjectProperty


#### VehicleComponents_AffectedVehicle

Type: ObjectProperty


#### VehicleDeparture

Type: ObjectProperty


#### VehicleDeparture_AffectedVehicle

Type: ObjectProperty


#### VehicleExplosion

Type: ObjectProperty


#### VehicleExplosion_AffectedVehicle

Type: ObjectProperty


#### VehicleMotion

Type: ObjectProperty


#### VehicleMotion_AffectedVehicle

Type: ObjectProperty


#### VehiclePassengers_AffectedVehicle

Type: ObjectProperty


#### VehicleSpeedChange

Type: ObjectProperty


#### VehicleSpeedChange_AffectedVehicle

Type: ObjectProperty


#### VehicleSpeed_AffectedVehicle

Type: DatatypeProperty

Range: <class 'float'>


#### VehicleSpillage

Type: ObjectProperty


#### VehicleSpillage_AffectedVehicle

Type: ObjectProperty


#### VehicleTransport

Type: ObjectProperty


#### VehicleTransport_AffectedVehicle

Type: ObjectProperty


#### drivingDirection_AffectedVehicle

Type: DatatypeProperty

Range: <class 'str'>


#### position_AffectedVehicle

Type: DatatypeProperty

Range: <class 'str'>


#### vehicleType_AffectedVehicle

Type: DatatypeProperty

Range: <class 'str'>


### Properties of Class_1

#### IsDetached_1

Type: DatatypeProperty

Range: <class 'bool'>


#### LoadedOn_1

Type: ObjectProperty

Range: HazardVehicle


#### VehicleLoadTyoe_1

Type: DatatypeProperty

Range: <class 'str'>


### Properties of Class_14

#### HasAction_14

Type: ObjectProperty

Range: Class_14-救助


#### HasResource_14

Type: ObjectProperty

Range: Class_14-医生


#### PlanName_14

Type: DatatypeProperty

Range: <class 'str'>


### Properties of Class_14-医生

#### AssociatedBehavior_14-医生

Type: ObjectProperty

Range: Class_14-救助


#### Location_14-医生

Type: DatatypeProperty

Range: <class 'str'>


#### ResourceQuantityOrQuality_14-医生

Type: DatatypeProperty

Range: <class 'float'>


#### ResourceType_14-医生

Type: DatatypeProperty

Range: <class 'str'>


#### ResourceUsageCondition_14-医生

Type: DatatypeProperty

Range: <class 'bool'>


### Properties of Class_14-救助

#### BehaviorType_14-救助

Type: DatatypeProperty

Range: <class 'str'>


#### Duration_14-救助

Type: DatatypeProperty

Range: <class 'float'>


#### EmergencyVehicles_14-救助

Type: ObjectProperty


#### Firefighting_14-救助

Type: ObjectProperty


#### ImplementationCondition_14-救助

Type: DatatypeProperty

Range: <class 'bool'>


#### ImplementingPersonnel_14-救助

Type: ObjectProperty


#### InvolvedMaterials_14-救助

Type: ObjectProperty


#### PersonnalRescue_14-救助

Type: ObjectProperty


#### RoadCleaning_14-救助

Type: ObjectProperty


#### RoadControl_14-救助

Type: ObjectProperty


#### RoadRepair_14-救助

Type: ObjectProperty


#### TargetOfImplementation_14-救助

Type: ObjectProperty


#### VehicleTowing_14-救助

Type: ObjectProperty


### Properties of Class_2

#### FacilityDamageStatus_2

Type: DatatypeProperty

Range: <class 'bool'>


#### FacilityLocation_2

Type: DatatypeProperty

Range: <class 'str'>


#### FacilityType_2

Type: DatatypeProperty

Range: <class 'str'>


#### RoadFacilityOf_2

Type: ObjectProperty


### Properties of Class_23

#### ClosureCondition_23

Type: DatatypeProperty

Range: <class 'bool'>


#### DesignSpeed_23

Type: DatatypeProperty

Range: <class 'float'>


#### IncludedFacilities_23

Type: ObjectProperty


#### IncludedLanes_23

Type: ObjectProperty


#### IncludedVehicles_23

Type: ObjectProperty


#### NumberOfLanes_23

Type: DatatypeProperty

Range: <class 'float'>


#### PollutionCondition_23

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadConstrucetionCondition_23

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadDamageCondition_23

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadMaintenanceConditon_23

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadName_23

Type: DatatypeProperty

Range: <class 'str'>


#### RoadType_23

Type: DatatypeProperty

Range: <class 'str'>


#### SegmentEndStakeNumber_23

Type: DatatypeProperty

Range: <class 'str'>


#### SegmentStartStakeNumber_23

Type: DatatypeProperty

Range: <class 'str'>


#### TrafficVolume_23

Type: DatatypeProperty

Range: <class 'float'>


### Properties of HazardVehicle

#### AbnormalSpeedCondition_HazardVehicle

Type: DatatypeProperty

Range: <class 'str'>


#### BreakdownCondition_HazardVehicle

Type: DatatypeProperty

Range: <class 'bool'>


#### CollideCondition_HazardVehicle

Type: DatatypeProperty

Range: <class 'bool'>


#### CombustionCondition_HazardVehicle

Type: DatatypeProperty

Range: <class 'bool'>


#### DrivingRoadSegment_HazardVehicle

Type: ObjectProperty

Range: hello


#### EmergencyPeriod_HazardVehicle

Type: DatatypeProperty

Range: <class 'str'>


#### IIIegalLaneOccupationCondition_HazardVehicle

Type: DatatypeProperty

Range: <class 'bool'>


#### RollOverCondition_HazardVehicle

Type: DatatypeProperty

Range: <class 'bool'>


#### SpillCondition_HazardVehicle

Type: DatatypeProperty

Range: <class 'bool'>


#### VehicleBreakdown

Type: ObjectProperty


#### VehicleBreakdown_HazardVehicle

Type: ObjectProperty


#### VehicleCargo_HazardVehicle

Type: ObjectProperty


#### VehicleCollision

Type: ObjectProperty

Range: Road


#### VehicleCollision_HazardVehicle

Type: ObjectProperty

Range: Road


#### VehicleComponents_HazardVehicle

Type: ObjectProperty


#### VehicleDeparture

Type: ObjectProperty


#### VehicleDeparture_HazardVehicle

Type: ObjectProperty


#### VehicleExplosion

Type: ObjectProperty


#### VehicleExplosion_HazardVehicle

Type: ObjectProperty


#### VehicleLaneChange

Type: ObjectProperty


#### VehicleLaneChange_HazardVehicle

Type: ObjectProperty


#### VehicleMotion

Type: ObjectProperty


#### VehicleMotion_HazardVehicle

Type: ObjectProperty


#### VehicleOverturn

Type: ObjectProperty

Range: Road


#### VehicleOverturn_HazardVehicle

Type: ObjectProperty

Range: Road


#### VehiclePassengers_HazardVehicle

Type: ObjectProperty


#### VehicleSpeedChange

Type: ObjectProperty


#### VehicleSpeedChange_HazardVehicle

Type: ObjectProperty


#### VehicleSpeed_HazardVehicle

Type: DatatypeProperty

Range: <class 'float'>


#### VehicleSpillage

Type: ObjectProperty


#### VehicleSpillage_HazardVehicle

Type: ObjectProperty


#### VehicleTransport

Type: ObjectProperty


#### VehicleTransport_HazardVehicle

Type: ObjectProperty


#### VehicleTurning

Type: ObjectProperty


#### VehicleTurning_HazardVehicle

Type: ObjectProperty


#### drivingDirection_HazardVehicle

Type: DatatypeProperty

Range: <class 'str'>


#### position_HazardVehicle

Type: DatatypeProperty

Range: <class 'str'>


#### vehicleType_HazardVehicle

Type: DatatypeProperty

Range: <class 'str'>


### Properties of Meteorology

#### AffectedArea_Meteorology

Type: ObjectProperty

Range: Road


#### Rainfall_Meteorology

Type: DatatypeProperty

Range: <class 'float'>


#### SnowfallIntensity_Meteorology

Type: DatatypeProperty

Range: <class 'str'>


#### Visibility_Meteorology

Type: DatatypeProperty

Range: <class 'float'>


#### WeatherType_Meteorology

Type: DatatypeProperty

Range: <class 'str'>


#### WindForce_Meteorology

Type: DatatypeProperty

Range: <class 'float'>


#### WindSpeed_Meteorology

Type: DatatypeProperty

Range: <class 'float'>


### Properties of Road

#### ClosureCondition_Road

Type: DatatypeProperty

Range: <class 'bool'>


#### DesignSpeed_Road

Type: DatatypeProperty

Range: <class 'float'>


#### IncludedFacilities_Road

Type: ObjectProperty


#### IncludedLanes_Road

Type: ObjectProperty


#### IncludedVehicles_Road

Type: ObjectProperty


#### NumberOfLanes_Road

Type: DatatypeProperty

Range: <class 'float'>


#### PollutionCondition_Road

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadConstrucetionCondition_Road

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadDamageCondition_Road

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadMaintenanceConditon_Road

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadName_Road

Type: DatatypeProperty

Range: <class 'str'>


#### RoadType_Road

Type: DatatypeProperty

Range: <class 'str'>


#### SegmentEndStakeNumber_Road

Type: DatatypeProperty

Range: <class 'str'>


#### SegmentStartStakeNumber_Road

Type: DatatypeProperty

Range: <class 'str'>


#### SpeedLimit_Road

Type: DatatypeProperty

Range: <class 'float'>


#### TrafficCapacity_Road

Type: DatatypeProperty

Range: <class 'float'>


#### TrafficVolume_Road

Type: DatatypeProperty

Range: <class 'float'>


#### TravelTime_Road

Type: DatatypeProperty

Range: <class 'float'>


### Properties of hello

#### ClosureCondition_hello

Type: DatatypeProperty

Range: <class 'bool'>


#### DesignSpeed_hello

Type: DatatypeProperty

Range: <class 'float'>


#### IncludedFacilities_hello

Type: ObjectProperty


#### IncludedLanes_hello

Type: ObjectProperty


#### IncludedVehicles_hello

Type: ObjectProperty


#### NumberOfLanes_hello

Type: DatatypeProperty

Range: <class 'float'>


#### PollutionCondition_hello

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadConstrucetionCondition_hello

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadDamageCondition_hello

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadMaintenanceConditon_hello

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadName_hello

Type: DatatypeProperty

Range: <class 'str'>


#### RoadType_hello

Type: DatatypeProperty

Range: <class 'str'>


#### SegmentEndStakeNumber_hello

Type: DatatypeProperty

Range: <class 'str'>


#### SegmentStartStakeNumber_hello

Type: DatatypeProperty

Range: <class 'str'>


#### TrafficVolume_hello

Type: DatatypeProperty

Range: <class 'float'>


### Properties of hoa

#### ClosureCondition_hoa

Type: DatatypeProperty

Range: <class 'bool'>


#### DesignSpeed_hoa

Type: DatatypeProperty

Range: <class 'float'>


#### IncludedFacilities_hoa

Type: ObjectProperty


#### IncludedLanes_hoa

Type: ObjectProperty


#### IncludedVehicles_hoa

Type: ObjectProperty


#### NumberOfLanes_hoa

Type: DatatypeProperty

Range: <class 'float'>


#### PollutionCondition_hoa

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadConstrucetionCondition_hoa

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadDamageCondition_hoa

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadMaintenanceConditon_hoa

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadName_hoa

Type: DatatypeProperty

Range: <class 'str'>


#### RoadType_hoa

Type: DatatypeProperty

Range: <class 'str'>


#### SegmentEndStakeNumber_hoa

Type: DatatypeProperty

Range: <class 'str'>


#### SegmentStartStakeNumber_hoa

Type: DatatypeProperty

Range: <class 'str'>


#### SpeedLimit_hoa

Type: DatatypeProperty

Range: <class 'float'>


#### TrafficCapacity_hoa

Type: DatatypeProperty

Range: <class 'float'>


#### TrafficVolume_hoa

Type: DatatypeProperty

Range: <class 'float'>


#### TravelTime_hoa

Type: DatatypeProperty

Range: <class 'float'>


### Properties of hob

#### ClosureCondition_hob

Type: DatatypeProperty

Range: <class 'bool'>


#### DesignSpeed_hob

Type: DatatypeProperty

Range: <class 'float'>


#### IncludedFacilities_hob

Type: ObjectProperty


#### IncludedLanes_hob

Type: ObjectProperty


#### IncludedVehicles_hob

Type: ObjectProperty


#### NumberOfLanes_hob

Type: DatatypeProperty

Range: <class 'float'>


#### PollutionCondition_hob

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadConstrucetionCondition_hob

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadDamageCondition_hob

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadMaintenanceConditon_hob

Type: DatatypeProperty

Range: <class 'bool'>


#### RoadName_hob

Type: DatatypeProperty

Range: <class 'str'>


#### RoadType_hob

Type: DatatypeProperty

Range: <class 'str'>


#### SegmentEndStakeNumber_hob

Type: DatatypeProperty

Range: <class 'str'>


#### SegmentStartStakeNumber_hob

Type: DatatypeProperty

Range: <class 'str'>


#### TrafficVolume_hob

Type: DatatypeProperty

Range: <class 'float'>


### Properties of passenger

#### AffiliatedVehicle_passenger

Type: ObjectProperty


#### CasualtyCondition_passenger

Type: DatatypeProperty

Range: <class 'bool'>


### Properties of plan1

#### HasAction_plan1

Type: ObjectProperty

Range: plan1-救助


#### HasResource_plan1

Type: ObjectProperty

Range: plan1-人员


#### PlanName_plan1

Type: DatatypeProperty

Range: <class 'str'>


### Properties of plan1-人员

#### AssociatedBehavior_plan1-人员

Type: ObjectProperty

Range: plan1-救助


#### Location_plan1-人员

Type: DatatypeProperty

Range: <class 'str'>


#### ResourceQuantityOrQuality_plan1-人员

Type: DatatypeProperty

Range: <class 'float'>


#### ResourceType_plan1-人员

Type: DatatypeProperty

Range: <class 'str'>


#### ResourceUsageCondition_plan1-人员

Type: DatatypeProperty

Range: <class 'bool'>


### Properties of plan1-救助

#### BehaviorType_plan1-救助

Type: DatatypeProperty

Range: <class 'str'>


#### Duration_plan1-救助

Type: DatatypeProperty

Range: <class 'float'>


#### EmergencyVehicles_plan1-救助

Type: ObjectProperty


#### Firefighting

Type: ObjectProperty


#### Firefighting_plan1-救助

Type: ObjectProperty


#### ImplementationCondition_plan1-救助

Type: DatatypeProperty

Range: <class 'bool'>


#### ImplementingPersonnel_plan1-救助

Type: ObjectProperty


#### InvolvedMaterials_plan1-救助

Type: ObjectProperty


#### PersonnalRescue

Type: ObjectProperty


#### PersonnalRescue_plan1-救助

Type: ObjectProperty


#### RoadCleaning

Type: ObjectProperty


#### RoadCleaning_plan1-救助

Type: ObjectProperty


#### RoadControl

Type: ObjectProperty


#### RoadControl_plan1-救助

Type: ObjectProperty


#### RoadRepair

Type: ObjectProperty


#### RoadRepair_plan1-救助

Type: ObjectProperty


#### TargetOfImplementation_plan1-救助

Type: ObjectProperty


#### VehicleTowing

Type: ObjectProperty


#### VehicleTowing_plan1-救助

Type: ObjectProperty


## Behaviors

## Rules

