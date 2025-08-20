# Master System Architecture Document

**Created**: 2025 08 08

## Master Diagram Header

**Master Diagram ID**: Master_System_Architecture_GTach
**Category**: System Architecture
**Version**: 1.0
**Status**: Active
**Created**: 2025 08 08
**Last Updated**: 2025 08 20
**Authority Level**: Master Document - Single Source of Truth

## Purpose and Authority

### Master Document Purpose
This master document serves as the authoritative single source of truth for the GTach system architecture, defining the complete system structure, functional domain organization, cross-platform abstraction layers, and high-level integration patterns that govern all subsidiary architectural documentation.

### Scope of Authority
This master document definitively governs:
- Overall system structure and functional domain boundaries
- Cross-platform development and deployment architecture
- High-level component relationships and integration patterns
- System-wide architectural principles and design constraints
- Authoritative reference for all subsidiary architecture diagrams

### Subsidiary Document Coordination
All subsidiary architecture diagrams must maintain consistency with this master document and reference this document as their authoritative source for system-level architectural decisions and component relationships.

## System Overview

### Master System View
The GTach system implements a comprehensive OBDII diagnostic interface with cross-platform development and deployment architecture. The system consists of two primary domains: the OBDII application providing vehicle diagnostics through display, communication, and core services, and the provisioning system enabling automated deployment and updates.

### Architectural Principles
- **Cross-Platform Compatibility**: Identical application logic across Mac development and Raspberry Pi deployment through platform abstraction
- **Embedded Systems Optimization**: Resource-efficient design for Pi hardware constraints with optimized memory and CPU usage
- **Thread Safety**: Comprehensive concurrent operation support across all system components
- **Hardware Abstraction**: Common interface patterns enabling mock implementations for development and real hardware for production
- **Modular Architecture**: Functional domain separation enabling independent development and testing

### Integration Points
- **OBDII-Provisioning Integration**: Application lifecycle management through provisioning system
- **Platform Abstraction Boundaries**: Cross-platform compatibility layers between development and production environments
- **Hardware Interface Points**: GPIO, display, and input device integration through standardized interfaces
- **Communication Protocols**: Bluetooth and OBD interface standardization across platforms

## Master Visual Documentation

### Primary Master Diagram
```mermaid
flowchart TD
    subgraph "Development Environment (Mac Mini M4)"
        subgraph "Provisioning Development"
            PackageCreator[Package Creator]
            VersionMgr[Version Manager]
            RepoMgr[Repository Manager]
            ArchiveMgr[Archive Manager]
        end
        
        subgraph "OBDII Application Development"
            subgraph "Display Development"
                DisplayMgrDev[Display Manager]
                ComponentsDev[Component Factory]
                RenderEngineDev[Render Engine]
                TouchCoordDev[Touch Coordinator]
                GraphicsDev[Graphics Engine]
                PerformanceDev[Performance Monitor]
            end
            
            subgraph "Communication Development"
                BluetoothDev[Bluetooth Manager]
                OBDDev[OBD Handler]
                DeviceStoreDev[Device Store]
                PairingDev[Pairing Manager]
                SystemBluetoothDev[System Bluetooth]
            end
            
            subgraph "Core Development"
                ThreadMgrDev[Thread Manager]
                WatchdogDev[Watchdog Enhanced]
                ConfigMgrDev[Configuration Manager]
            end
            
            subgraph "Utils Development"
                PlatformUtilsDev[Platform Utils]
                ServicesDev[Service Registry]
                DependencyDev[Dependency Manager]
            end
        end
    end
    
    subgraph "Platform Abstraction Layer"
        PlatformDetect[Platform Detection]
        ConfigAbstract[Configuration Abstraction]
        InterfaceAbstract[Interface Abstraction]
        HardwareAbstract[Hardware Abstraction]
        ServiceAbstract[Service Abstraction]
    end
    
    subgraph "Distribution Layer"
        PackageDist[Package Distribution]
        SecureTransfer[Secure Transfer]
        IntegrityVerify[Integrity Verification]
        VersionValidation[Version Validation]
    end
    
    subgraph "Deployment Environment (Raspberry Pi)"
        subgraph "Provisioning Production"
            Installer[Package Installer]
            UpdateMgr[Update Manager]
            RollbackMgr[Rollback Manager]
        end
        
        subgraph "OBDII Application Production"
            subgraph "Display Production"
                DisplayMgr[Display Manager]
                Components[Component Factory]
                RenderEngine[Render Engine]
                TouchCoord[Touch Coordinator]
                Graphics[Graphics Engine]
                Performance[Performance Monitor]
            end
            
            subgraph "Communication Production"
                BluetoothMgr[Bluetooth Manager]
                OBDHandler[OBD Handler]
                DeviceStore[Device Store]
                PairingMgr[Pairing Manager]
                SystemBluetooth[System Bluetooth]
            end
            
            subgraph "Core Production"
                ThreadMgr[Thread Manager]
                Watchdog[Watchdog Enhanced]
                ConfigMgr[Configuration Manager]
            end
            
            subgraph "Utils Production"
                PlatformUtils[Platform Utils]
                Services[Service Registry]
                Dependency[Dependency Manager]
            end
        end
        
        subgraph "Hardware Interfaces"
            GPIO[GPIO Controller]
            HyperPixel[HyperPixel Display]
            TouchInterface[Touch Interface]
            BluetoothHW[Bluetooth Hardware]
        end
    end
    
    %% Development to Abstraction
    PackageCreator --> PlatformDetect
    VersionMgr --> ConfigAbstract
    DisplayMgrDev --> HardwareAbstract
    BluetoothDev --> InterfaceAbstract
    ThreadMgrDev --> ServiceAbstract
    PlatformUtilsDev --> PlatformDetect
    
    %% Abstraction to Distribution
    PlatformDetect --> PackageDist
    ConfigAbstract --> SecureTransfer
    InterfaceAbstract --> IntegrityVerify
    ServiceAbstract --> VersionValidation
    
    %% Distribution to Production
    PackageDist --> Installer
    SecureTransfer --> UpdateMgr
    IntegrityVerify --> RollbackMgr
    
    %% Platform Abstraction to Production
    HardwareAbstract --> DisplayMgr
    HardwareAbstract --> TouchCoord
    InterfaceAbstract --> BluetoothMgr
    InterfaceAbstract --> OBDHandler
    ServiceAbstract --> ThreadMgr
    ConfigAbstract --> ConfigMgr
    
    %% Production to Hardware
    DisplayMgr --> HyperPixel
    TouchCoord --> TouchInterface
    BluetoothMgr --> BluetoothHW
    OBDHandler --> GPIO
    ThreadMgr --> GPIO
    
    %% OBDII Internal Integration
    DisplayMgr --> Components
    Components --> RenderEngine
    RenderEngine --> Graphics
    TouchCoord --> Performance
    BluetoothMgr --> DeviceStore
    DeviceStore --> PairingMgr
    ThreadMgr --> Watchdog
    ConfigMgr --> Services
    
    %% Cross-cutting Integration
    Installer --> DisplayMgr
    Installer --> BluetoothMgr
    Installer --> ThreadMgr
    UpdateMgr --> ConfigMgr
    RollbackMgr --> Watchdog
```

### Supporting Master Views

#### Cross-Platform Abstraction View
```mermaid
flowchart LR
    subgraph "Development Interfaces"
        MockGPIO[Mock GPIO]
        MockDisplay[Mock Display]
        MockInput[Mock Input]
        DevConfig[Dev Configuration]
    end
    
    subgraph "Abstraction Layer"
        CommonAPI[Common API]
        PlatformFactory[Platform Factory]
        ConfigLoader[Config Loader]
        InterfaceAdapter[Interface Adapter]
    end
    
    subgraph "Production Interfaces"
        RealGPIO[Real GPIO]
        RealDisplay[Real Display]
        RealInput[Real Input]
        ProdConfig[Prod Configuration]
    end
    
    MockGPIO --> CommonAPI
    MockDisplay --> CommonAPI
    MockInput --> CommonAPI
    DevConfig --> ConfigLoader
    
    CommonAPI --> InterfaceAdapter
    PlatformFactory --> InterfaceAdapter
    ConfigLoader --> InterfaceAdapter
    
    InterfaceAdapter --> RealGPIO
    InterfaceAdapter --> RealDisplay
    InterfaceAdapter --> RealInput
    InterfaceAdapter --> ProdConfig
```

#### Provisioning Integration View
```mermaid
flowchart TD
    subgraph "Development Workflow"
        DevCode[Development Code]
        GitCommit[Git Commit]
        Package[Package Creation]
    end
    
    subgraph "Provisioning Pipeline"
        Version[Version Management]
        Repo[Repository Storage]
        Dist[Distribution]
    end
    
    subgraph "Deployment Workflow"
        Install[Installation]
        Validate[Validation]
        Operate[Operation]
    end
    
    DevCode --> GitCommit
    GitCommit --> Package
    Package --> Version
    Version --> Repo
    Repo --> Dist
    Dist --> Install
    Install --> Validate
    Validate --> Operate
```

### Master Legend and Notation
- **Functional Domain**: Provisioning, Display, Communication, Core system areas
- **Platform Abstraction**: Cross-platform compatibility layers enabling Mac-to-Pi deployment
- **Integration Point**: Critical boundaries between development, abstraction, distribution, and production
- **Authority Level**: Master document authoritative elements governing system architecture

## Subsidiary Document Governance

### Subsidiary Document Registry
- **Provisioning_System_Architecture**: Detailed provisioning system architecture (Active)
- **Provisioning_Component_Interaction**: Component interfaces and data flows (Active)
- **Provisioning_Data_Flow**: Comprehensive workflow visualization (Active)
- **Display_System_Architecture** (Required): Display subsystem with components, graphics, rendering, and touch coordination
- **Communication_System_Architecture** (Required): Bluetooth, OBD, device store, and pairing management
- **Core_Services_Architecture** (Required): Thread management, watchdog, and configuration services
- **Hardware_Interface_Specifications** (Required): GPIO, HyperPixel, and touch interface diagrams

### Abstraction Level Management
All subsidiary architecture diagrams must maintain consistent abstraction levels that provide detailed views of components shown at high level in this master document.

### Consistency Requirements
Subsidiary diagrams must:
- Reference this master document as authoritative source
- Maintain consistent component naming and relationships
- Align with architectural principles defined in this master
- Coordinate updates through master document change procedures

### Update Coordination Procedures
Changes to this master document require:
- Impact assessment on all subsidiary architecture diagrams
- Validation of continued consistency across architectural documentation
- Coordination with cross-platform development requirements
- Integration with hardware interface specifications

### Cross-Platform Master Specifications

#### Development Environment Authority
**Mac Mini M4 Architecture**: Complete development infrastructure including package creation tools, mock hardware interfaces, version management systems, and repository operations supporting full provisioning system development and testing.

**Development Integration**: Seamless integration with Claude Desktop strategic planning, Claude Code tactical implementation, GitHub Desktop version control, and Obsidian documentation management per established protocols.

#### Deployment Environment Authority
**Raspberry Pi Architecture**: Production embedded system implementing real hardware interfaces, GPIO control, display management, communication protocols, and system services with optimized resource utilization.

**Production Integration**: Hardware-specific implementations including GPIO interfaces per Protocol 10 specifications, display subsystems, input devices, and communication protocols validated through comprehensive testing procedures.

#### Platform Abstraction Definition
**Abstraction Layer**: Comprehensive platform abstraction enabling identical application logic across development and deployment environments through common APIs, configuration management, and interface standardization.

## Integration with Project Architecture

### Protocol Authority
This master document authoritatively supports:
- Protocol 1 project structure through architectural alignment
- Protocol 6 cross-platform development through abstraction definition
- Protocol 10 hardware documentation through interface specification

### Implementation Authority
This master document definitively guides:
- System component implementation approaches
- Cross-platform compatibility requirements
- Hardware integration patterns

### Testing Authority
This master document establishes:
- Multi-layer testing architecture requirements
- Cross-platform validation procedures
- System integration testing approaches

## Master Document Maintenance

### Authority Validation Procedures
This master document authority is validated through:
- Quarterly review of system architecture accuracy
- Validation against current implementation specifications
- Cross-platform compatibility verification
- Hardware integration requirement confirmation

### Update Authorization Requirements
Changes to this master document require:
- Technical review by system architect
- Impact assessment on subsidiary documentation
- Validation of cross-platform compatibility implications
- Integration with protocol requirement changes

### Subsidiary Impact Assessment
Master document changes require assessment of impact on:
- All subsidiary architecture diagrams
- Component interaction specifications
- Hardware interface definitions
- Cross-platform implementation requirements

### Version Control Authority
Master document changes are tracked through:
- Git version control with detailed change rationale
- Cross-reference to related implementation changes
- Integration with iteration-based development workflow
- Coordination with protocol update procedures

## Quality Assurance and Governance

### Master Document Review Requirements
This master document undergoes:
- Monthly accuracy validation against implementation
- Quarterly comprehensive review for completeness
- Annual architectural assessment for evolution needs
- Integration validation with hardware specifications

### Conflict Resolution Procedures
Conflicts between this master document and other documentation are resolved by:
- Establishing master document authority precedence
- Technical review of conflicting specifications
- Integration assessment with project requirements
- Update coordination across affected documentation

### Authority Verification
Master document authority is verified through:
- Implementation consistency validation
- Cross-platform compatibility confirmation
- Hardware integration requirement alignment
- Protocol compliance verification

### Completeness Validation
Master document completeness is ensured through:
- Coverage verification of all system components
- Cross-platform requirement specification completeness
- Hardware integration pattern definition completeness
- Subsidiary document governance adequacy

## References and Dependencies

### Authoritative Sources
- Protocol 1: Project Structure Standards
- Protocol 6: Cross-Platform Development Standards
- Protocol 10: Hardware Documentation and Integration Standards

### Governed Documents
[To be populated as subsidiary architecture diagrams are created]

### External Authority References
- Raspberry Pi hardware specifications
- Mac development environment requirements
- GPIO interface standards

---

**Master Document Status**: Active - OBDII Application Architecture Integrated
**Authority Verification Date**: 2025-08-20
**Next Master Review**: 2025-09-20
**Subsidiary Coordination Status**: Provisioning subsidiaries complete, OBDII component diagrams required

---

**Copyright**: Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
