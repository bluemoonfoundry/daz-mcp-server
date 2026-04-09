/**
 * Daz Studio TypeScript Definitions
 * Generated Specification
 */

// --- START OF DYNAMIC TYPE ALIASES ---
type any_obj = any;
type AccessMode = any;
type AlignmentFlags = any;
type AlignX = any;
type AlignY = any;
type AlignZ = any;
type AnimationBlendMode = any;
type AreaShape = any;
type AssetType = any;
type AttenuateMode = any;
type AutoFormattingFlag = any;
type BarStyle = any;
type BaseType = any;
type BlendMode = any;
type bool = any;
type ButtonStyle = any;
type cameracube_dz = any;
type CameraDimension = any;
type CameraType = any;
type Communication = any;
type CompatibilityBaseTypes = any;
type ContainerState = any;
type ContentReplaceMode = any;
type contenttab_dz = any;
type ControllerEffect = any;
type CoordinateSpace = any;
type CursorMoveOperation = any;
type Direction = any;
type DirectoryTypes = any;
type DividerOrientation = any;
type DockArea = any;
type DockSide = any;
type DzAppSettingsMgr = any;
type DzBakerOptions = any;
type DzElementDuplicateContext = any;
type DzFileLoadFilter = any;
type DzOpenMethod = any;
type DzPaneGroupDlg = any;
type DzRenderSettings = any;
type DzShaderParamType = any;
type DzShaderType = any;
type DzWeightMapContext = any;
type EchoMode = any;
type elementclipboard_dz = any;
type ERCKeyInterpolation = any;
type ERCType = any;
type expression = any;
type FileError = any;
type FileType = any;
type Filters = any;
type float = any;
type FloorStyle = any;
type FolderType = any;
type FollowMode = any;
type Format = any;
type GammaCorrection = any;
type geometryregion_dz = any;
type GeometryType = any;
type GraphicsMode = any;
type GrayscaleMode = any;
type HeadlightMode = any;
type InfluenceMode = any;
type InsertPolicy = any;
type int = any;
type InterpolationType = any;
type iprrenderhandler_dz = any;
type ItemsMode = any;
type KeyboardModifiers = any;
type Layout = any;
type LayoutMode = any;
type LightType = any;
type LineWrapMode = any;
type LoadMode = any;
type MapType = any;
type MessageSeverity = any;
type MetadataTypes = any;
type MirroringType = any;
type Mode = any;
type Modifications = any;
type MouseButton = any;
type NameEditScope = any;
type naturalspline_dz = any;
type NodeClickMode = any;
type NodeType = any;
type OGLTexQuality = any;
type OpenMode = any;
type OperatingSystem = any;
type Orientation = any;
type OverwriteMode = any;
type PartFlags = any;
type pbuffer_dz = any;
type Permissions = any;
type PixelFilter = any;
type PixmapMode = any;
type PixmapState = any;
type Platform = any;
type PrimitiveType = any;
type ProductInstallStates = any;
type ProductMetadataType = any;
type propertyclipboard_dz = any;
type PropertyResetFlags = any;
type propertysidenavhierarchy_dz = any;
type PropertyValueSettingsFlags = any;
type QAbstractButton = any;
type QDMode = any;
type QLayout = any;
type ReleaseCycle = any;
type ReleaseEdition = any;
type RenameAction = any;
type RenderImgTarget = any;
type RenderMovTarget = any;
type RenderPriority = any;
type RenderStyle = any;
type RenderType = any;
type renderview_dz = any;
type ResizeMode = any;
type Rotation = any;
type sceneshader_dz = any;
type SchemeType = any;
type ScriptFileMode = any;
type ScriptLanguage = any;
type SearchOptions = any;
type SegmentStyle = any;
type SelectionMode = any;
type ShaderType = any;
type ShadeStyle = any;
type ShadowType = any;
type SizeAdjustPolicy = any;
type SortFlags = any;
type SortOrder = any;
type SortType = any;
type SourceMorphTransferType = any;
type SourceSubdivisionMode = any;
type startic = any;
type Status = any;
type StopModeCMS = any;
type SubDAlgorithm = any;
type SubDEdgeInterpolation = any;
type SubDNormalSmoothingMode = any;
type TabBarPosition = any;
type TabPosition = any;
type TextElideMode = any;
type TextFormat = any;
type TextInteractionFlags = any;
type textureconvertoroptions_dz = any;
type ToggleState = any;
type ToggleType = any;
type ToolBarMode = any;
type TransformType = any;
type Type = any;
type Undefined = any;
type UnitSize = any;
type ViewMouseBtnAccelerator = any;
type ViewMouseModifier = any;
type ViewOperation = any;
type WidgetType = any;
type WidthMode = any;
type WrapMode = any;
type wsmodifier_dz = any;
type XYZInterest = any;
// --- END OF DYNAMIC TYPE ALIASES ---

/**
 * A Dz3DViewport is a widget for displaying three dimensional objects using OpenGL and interacting with those objects using DzViewTool subclasses. See Also: DzViewport :: get3DViewport ()
 */
declare class Dz3DViewport {
    aspectOn(): boolean;
    axesOn: boolean;
    background: { r: number, g: number, b: number, a: number };
    floorStyle: FloorStyle;
    shadeStyle: ShadeStyle;
    showPoseTool: boolean;
    thirdsGuideOn: boolean;
    toolBarMode: ToolBarMode;

    aimCamera(): void;
    aimCameraAtBox(box: DzBox3): void;
    aimCameraAtPrimaryNode(): void;
    captureImage(): Image;
    currentDimensions(): DzInt2;
    endNavigation(): void;
    frameCamera(): void;
    frameCameraOnBox(box: DzBox3): void;
    frameCameraOnSelectedNodes(): void;
    getAspectFrameRect(): Rect;
    getCamera(): DzCamera;
    getCameraCube(): cameracube_dz;
    getDrawStyle(): DzDrawStyle;
    getUserDrawStyle(): string;
    getViewport(): DzViewport;
    hardwareRender(handler: DzRenderHandler): boolean;
    hardwareRenderWithOptions(handler: DzRenderHandler, options: DzRenderOptions, camera: DzCamera, style: DzDrawStyle): boolean;
    isHardwareRenderable(): boolean;
    isNavigating(): boolean;
    pickOnFacet(pnt: Point): number;
    pickOnGizmo(pnt: Point): number;
    pickOnMaterial(pnt: Point): DzMaterial;
    pickOnNode(pnt: Point): DzNode;
    pickOnNode(pnt: Point, useSelectionMaps: boolean): DzNode;
    renderThumbnail(handler: DzRenderHandler): boolean;
    resetCamera(): void;
    setCamera(cam: string): void;
    setCamera(cam: DzCamera): void;
    setDrawStyle(style: DzDrawStyle): void;
    setUserDrawStyle(description: string): boolean;
    mouseIsDown(): boolean;

    // SIGNALS
    activeCameraChanged(cam: DzCamera): void;
    activeCameraProjectionChanged(): void;
    activeCameraTransformChanged(): void;
    aspectOnChanged(onOff: boolean): void;
    axesOnChanged(onOff: boolean): void;
    backgroundColorChanged(color: { r: number, g: number, b: number, a: number }): void;
    contextMenuAboutToShow(menu: DzMenu, pos: Point): void;
    currentDimensionsChanged(): void;
    dimensionsChanged(): void;
    drawStyleChanged(style: DzDrawStyle): void;
    floorStyleChanged(style: FloorStyle): void;
    thirdsGuideOnChanged(onOff: boolean): void;
    toolBarDocked(onOff: boolean): void;
    toolModeChanged(mode: ToolBarMode): void;
    viewChanged(): void;
}

/**
 * This render handler is a DzImageRenderHandler that is the size of the aspect frame for the given viewport, and paints all data passed to it over the current view.
 */
declare class Dz3DViewRenderHandler {
    getLeftOffset(): number;
    getTopOffset(): number;
    getView(): renderview_dz;
    getViewport(): DzViewport;
}

/**
 * TODO: Add detailed description.
 */
declare class DzAbstractAssetContainer {
    canCopyContainers(): boolean;
    canDeleteContainer: boolean;
    canInsertSubContainer: boolean;
    canModifyAssets: boolean;
    canRenameContainer: boolean;
    id: any;
    removeAssetCausesDelete: boolean;
    tooltip: string;
    useCount: number;

    clearRebuildableAssets(): boolean;
    createNewChildContainer(containerName: string): boolean;
    getAsset(index: number): DzAsset;
    getAssets(): any[];
    getChildContainer(index: number): DzAbstractAssetContainer;
    getChildContainers(): any[];
    getChildIconSize(): Size;
    getContainerName(): string;
    getIDPath(): any[];
    getNumAssets(): number;
    getNumChildContainers(): number;
    getOwner(): DzAbstractAssetContainer;
    getSmallChildIconSize(): Size;
    getSupportFile(): string;
    hasAsset(asset: DzAsset): boolean;
    hasChildContainers(): boolean;
    ignoreAssetConflicts(): boolean;
    initChildren(): boolean;
    insertAsset(asset: DzAsset): boolean;
    insertChildContainer(container: DzAbstractAssetContainer): boolean;
    isFileSystemBased(): boolean;
    moveFromParent(child: DzAbstractAssetContainer): boolean;
    removeAsset(asset: DzAsset): boolean;
    removeAssetOnCut(toContainer: DzAbstractAssetContainer): boolean;
    removeChildContainer(container: DzAbstractAssetContainer): boolean;
    rename(name: string): boolean;
    renameAsset(asset: DzAsset, newAssetName: string): boolean;
    renameChildContainer(container: DzAbstractAssetContainer, name: string): boolean;
    setContainerName(name: string): void;
    update(): boolean;
    updateAssets(): boolean;

    // SIGNALS
    assetIconChanged(asset: DzAsset): void;
    assetRenamed(asset: DzAsset, index: number): void;
    beginAssetAdd(start: number, end: number): void;
    beginAssetRemove(start: number, end: number): void;
    beginChildContainerAdd(container: DzAbstractAssetContainer, start: number, end: number): void;
    beginChildContainerRemove(container: DzAbstractAssetContainer, start: number, end: number): void;
    childContainerAboutToBeRemoved(childContainer: DzAbstractAssetContainer): void;
    childContainerRemoved(childContainer: DzAbstractAssetContainer): void;
    endAssetAdd(): void;
    endAssetRemove(): void;
    endChildContainerAdd(): void;
    endChildContainerRemove(): void;
    iconChanged(container: DzAbstractAssetContainer): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzAbstractNodeEditorPane {
    displaySeparate(): boolean;
    getContentTab(): contenttab_dz;
    getEditorGuidePage(): DzGuidePage;
    getInfoDivider(): DzInfoDivider;
    getNodeEditor(): propertysidenavhierarchy_dz;
    getPresetGuidePage(): DzGuidePage;
    setCurrentTab(which: number): void;
    showHidden(onOff: boolean): void;
    showingHidden(): boolean;
    toggleDisplaySeparate(): void;
    toggleShowHidden(): void;

    // SIGNALS
    assetHoverChanged(asset: DzAsset): void;
    currentTabChanged(which: number): void;
    showingHiddenChanged(onOff: boolean): void;
}

/**
 * This class represents an action that the user can perform in the interface via pressing a hot key or clicking on a menu/toolbar item. All action items are added to a list of interface actions which the user can customize. The user can specify their own keyboard shortcut or 'Hot Key' for the action, and any action item can be moved into a custom toolbar, as well as appear in the main menu. See Also: Sample: Action Trigger DzActionMgr :: getAction () DzActionMgr :: findAction ()
 */
declare class DzAction {
    actionGroup(): string;
    autoRepeat: boolean;
    checkable: boolean;
    checked: boolean;
    defaultMenu: string;
    defaultMenus: any[];
    defaultSettings: any;
    defaultShortcut: string;
    defaultToolBar: string;
    defaultToolBars: any[];
    description: string;
    documentationUrl: string;
    enabled: boolean;
    iconFile: string;
    iconMap: any;
    iconText: string;
    iconVisibleInMenu: boolean;
    shortcut: string;
    simpleText: string;
    statusTip: string;
    styleIcon: number;
    text: string;
    toolTip: string;
    triggerSettings: any;
    visible: boolean;
    whatsThis: string;

    hasModifier(): boolean;
    hover(): void;
    modifierDescription(modifiers: number): string;
    setChecked(onOff: boolean): void;
    setDisabled(onOff: boolean): void;
    setEnabled(onOff: boolean): void;
    setOff(onOff: boolean): void;
    setVisible(onOff: boolean): void;
    toggle(): void;
    trigger(): void;
    triggerWithSettings(settings: any): void;

    // SIGNALS
    changed(): void;
    enabled(onOff: boolean): void;
    hovered(): void;
    preExecute(): void;
    toggled(checked: boolean): void;
    triggered(checked: boolean): void;
}

/**
 * See Also: DzActionMgr :: getMenu () DzPane :: getOptionsMenu () DzViewTool :: getOptionsMenu () DzPersistentMenu :: getActionMenu ()
 */
declare class DzActionMenu {
    isDefault(): boolean;
    menuType: number;

    appendItemsFromMenu(menu: DzActionMenu): void;
    clear(): void;
    exec(): void;
    exec(pos: Point): void;
    findOrCreateSubMenu(path: string, asDefault: boolean): DzActionMenu;
    findSubMenu(path: string): DzActionMenu;
    getItem(i: number): DzActionMenuItem;
    getItemList(): any[];
    getNumItems(): number;
    getParentItem(): DzActionMenuItem;
    getPath(): string;
    hasItems(): boolean;
    insertAction(identifier: string, i: number): void;
    insertCustomAction(guid: string, i: number): void;
    insertFileMergeAction(fileName: string, label: string, i: number): void;
    insertFileOpenAction(fileName: string, label: string, i: number): void;
    insertItem(item: DzActionMenuItem, i: number): void;
    insertMenu(label: string, menu: DzActionMenu, i: number): void;
    insertSeparator(i: number): void;
    insertSubMenu(label: string, menu: DzActionMenu, asDefault: boolean, i: number): void;
    moveItem(item: DzActionMenuItem, i: number): void;
    removeItem(item: DzActionMenuItem): void;
    simplifySeparators(): void;

    // SIGNALS
    defaultChanged(yesNo: boolean): void;
    itemListChanged(): void;
}

/**
 * Action Menu Items are registered with a DzActionMenu and are available to access via methods on that class.
 */
declare class DzActionMenuItem {
    action(): string;
    isDefault: boolean;
    label: string;
    type: Type;

    getParentMenu(): DzActionMenu;
    getSubMenu(): DzActionMenu;
    loadFile(): void;
    setSubMenu(menu: DzActionMenu): void;
}

/**
 * Responsible for the management of actions that the user can perform in the interface by pressing the key combination specified by its shortcut or by clicking on a menu/toolbar item. There is only one instance of this manager in an application. This instance is created and owned by DzMainWindow . Request the instance via DzMainWindow :: getActionMgr (). See Also: Global :: MainWindow DzAction Samples: Actions
 */
declare class DzActionMgr {
    legalizeName(name: string): startic;
    addCustomAction(text: string, desc: string, script: string, isFile: boolean, shortcut: string, iconFile: string): string;
    clearActiveMenu(): void;
    findAction(identifier: string): DzAction;
    findActionsForShortcut(shortcut: string): any[];
    findCustomAction(guid: string): number;
    findPaneAction(identifier: string): DzAction;
    findPersistentMenu(className: string): DzPersistentMenu;
    findViewToolAction(className: string): DzAction;
    getAction(index: number): DzAction;
    getActiveMenu(): DzActionMenu;
    getCustomAction(guid: string): number;
    getCustomActionByIndex(index: number): DzAction;
    getCustomActionDescription(index: number): string;
    getCustomActionFile(index: number): string;
    getCustomActionIcon(index: number): string;
    getCustomActionName(index: number): string;
    getCustomActionScript(index: number): string;
    getCustomActionShortcut(index: number): string;
    getCustomActionShowTextWithIcon(index: number): number;
    getCustomActionText(index: number): string;
    getDocumentationUrl(): string;
    getMenu(): DzActionMenu;
    getNumActions(): number;
    getNumCustomActions(): number;
    getNumPersistentMenus(): number;
    getPersistentMenu(index: number): DzPersistentMenu;
    loadInterfaceFile(filename: string, overrideDefaults: boolean): boolean;
    removeAllCustomActions(): void;
    removeCustomAction(index: number): void;
    saveActionsFile(filename: string): boolean;
    saveCustomActionsFile(filename: string): boolean;
    saveInterfaceFiles(): boolean;
    saveMenusFile(filename: string): boolean;
    saveToolBarsFile(filename: string): boolean;
    setAccel(className: string, key: string): void;
    setActiveMenu(menu: DzActionMenu): void;
    setCustomActionDescription(index: number, desc: string): void;
    setCustomActionIcon(index: number, iconFile: string): void;
    setCustomActionScript(index: number, script: string, isFile: boolean): void;
    setCustomActionShortcut(index: number, shortcut: string): void;
    setCustomActionShowTextWithIcon(index: number, onOff: boolean): void;
    setCustomActionText(index: number, text: string): void;
    unsetAccel(key: string): void;

    // SIGNALS
    customActionAdded(name: string): void;
    customActionListChanged(): void;
    customActionRemoved(name: string): void;
}

/**
 * Defines the layout of Toolbars, Pane Groups, Panes, Viewports and the active View Tool within an Activity of the interface. See Also: DzPaneMgr DzPaneGroup DzPane DzToolBar DzDockBar DzActionMgr DzViewportMgr
 */
declare class DzActivityLayout {
    description(): string;
    label: string;

    clearMemorizedState(): void;
    isToolBarEnabled(toolbar: string): boolean;
    setToolbarEnabled(toolbar: string, onOff: boolean): void;

    // SIGNALS
    labelChanged(label: string): void;
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureLayer :: BlendAdd instead.
 */
declare class DzAddBlend {
}

/**
 * See Also: DzExportMgr :: findExporterByClassName () DzExportMgr :: findExporter () Attention: This class is provided by the Alembic Exporter for DAZ Studio plugin.
 */
declare class DzAlembicExporter {
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureLayer :: BlendAlpha instead.
 */
declare class DzAlphaBlend {
}

/**
 * Derived from QApplication , this class embodies the main event loop, and owns application-wide settings and objects not directly related to the user interface. Can be directly accessed using the Global :: App variable.
 */
declare class DzApp {
    appName(): string;
    cloudName: string;
    exitCode: number;
    logSize: number;
    longVersionString: string;
    orgName: string;
    scriptArgs: any[];
    systemLocaleName: string;
    version: number;
    version64: number;
    versionString: string;

    durationToString(mSecs: number, simplified: boolean, useLocale: boolean): string;
    getPlatformVersion(): DzVersion;
    getVersion(): DzVersion;
    hasActiveModalWidget(): boolean;
    bitArchitecture(): number;
    bitArchitectureString(): string;
    byteSizeToString(bytes: number): string;
    canShowSceneBuilder(definition: any): boolean;
    clearDelayedDeleteStack(doProgress: boolean): void;
    clearPixmapCache(): void;
    cpuInfo(): any;
    createDigest(tokens: any[]): string;
    createDigest(data: ByteArray): string;
    createUuid(): string;
    debug(message: string): void;
    delayedExit(exitCode: number): void;
    enableMultiThreading(onOff: boolean): void;
    error(message: string): void;
    fatal(message: string): void;
    flushLogBuffer(): boolean;
    getAbsoluteScriptPath(scriptName: string): string;
    getAppDataInstancePath(): string;
    getAppDataPath(): string;
    getApplicationBaseName(): string;
    getApplicationDataName(): string;
    getAssetIOMgr(): DzAssetIOMgr;
    getAssetMgr(): DzAssetMgr;
    getAuthenticationMgr(): DzAuthenticationMgr;
    getCallBackMgr(): DzCallBackMgr;
    getCloudLogFilename(): string;
    getCommonUserDocumentPath(): string;
    getContentMgr(): DzContentMgr;
    getCurrentAuthor(): DzAuthor;
    getDataFolderName(): string;
    getDataFolderPath(): string;
    getDataFolderPathBase(): string;
    getDAZDataPath(): string;
    getDefaultTempPath(): string;
    getDeviceMgr(): DzDeviceMgr;
    getDialogParent(): QWidget;
    getDocumentationPath(): string;
    getDocumentationUrl(): string;
    getDocumentsPath(): string;
    getExportMgr(): DzExportMgr;
    getFileIOPresetMgr(): DzFileIOPresetMgr;
    getGeneratedScriptsPath(): string;
    getGeneratedShadersPath(): string;
    getGraphicsMode(): GraphicsMode;
    getHelpMgr(): DzHelpMgr;
    getHomePath(): string;
    getImageMgr(): DzImageMgr;
    getImportMgr(): DzImportMgr;
    getInterface(): DzMainWindow;
    getLoadSavePath(): string;
    getLogFilename(): string;
    getMultiMediaMgr(): DzMultiMediaMgr;
    getPluginMgr(): DzPluginMgr;
    getPluginsPath(): string;
    getProgramDataAppInstancePath(): string;
    getProgramDataAppPath(): string;
    getProgramDataPath(): string;
    getRenderMgr(): DzRenderMgr;
    getResourcesPath(): string;
    getScriptsPath(): string;
    getShadersPath(): string;
    getSimulationMgr(): DzSimulationMgr;
    getStyle(): DzStyle;
    getStyleDefinition(): string;
    getStyleDefinitionList(): any[];
    getTempFilename(): string;
    getTempPath(): string;
    getTempRenderFilename(): string;
    getTempShadersPath(): string;
    getUtilitiesPath(): string;
    instanceName(): string;
    instanceNameSuffix(): string;
    isClosing(): boolean;
    isEmittingLogMessages(): boolean;
    isKeyDown(key: number): boolean;
    isKeySequenceDown(sequence: string): boolean;
    isMultiThreadingEnabled(): boolean;
    isRegistered(): boolean;
    isRunning(): boolean;
    isSlave(): boolean;
    isStarting(): boolean;
    isValidGuid(data: string): boolean;
    log(message: string): void;
    logMessageBox(category: string, title: string, text: string, buttonTexts: any[], immediate: boolean): void;
    logPathInfo(label: string, path: string): void;
    modifierKeyState(): number;
    operatingSystem(): OperatingSystem;
    operatingSystemString(): string;
    platform(): Platform;
    postScriptEvent(evaluate: boolean, script: string, args: any[]): void;
    releaseCycle(): ReleaseCycle;
    releaseCycleInstanceString(): string;
    releaseCycleInstanceSuffix(): string;
    releaseCycleInstanceSuffixStripped(): string;
    releaseCycleLocaleString(): string;
    releaseCycleString(): string;
    releaseCycleSuffix(): string;
    releaseCycleSuffixStripped(): string;
    releaseEdition(): ReleaseEdition;
    releaseEditionLocaleString(): string;
    releaseEditionString(): string;
    restoreDefaultTempPath(): void;
    setLoadSavePath(path: string): void;
    setStyleDefinition(name: string): boolean;
    setTempPath(tempPath: string): boolean;
    showInNativeBrowser(absFilePath: string): boolean;
    showPrompts(): boolean;
    showSceneBuilder(definition: any, asEvent: boolean): any[];
    showURL(url: string): void;
    statusLine(message: string, addToLog: boolean): void;
    usingInterface(): boolean;
    verbose(message: string): void;
    warning(message: string): void;
    writeConfigScript(configScriptFilename: string): boolean;
    writeToLog(message: string): void;
    writeToLog(severity: MessageSeverity, category: string, message: string, immediate: boolean): void;
    writeToLog(message: string, immediate: boolean): void;
    writeToLog(severity: MessageSeverity, message: string, immediate: boolean): void;
    getSaveFilterMgr(): DzSaveFilterMgr;
    getAppSettingsMgr(): DzAppSettingsMgr;

    // SIGNALS
    closing(): void;
    debugMessage(message: string, category: string): void;
    errorMessage(message: string, category: string): void;
    eventLoopStarted(): void;
    fatalMessage(message: string, category: string): void;
    infoMessage(message: string, category: string): void;
    mouseEvent(): void;
    multiThreadingChanged(onOff: boolean): void;
    sceneBuilderAccepted(selections: any[]): void;
    sceneBuilderRejected(): void;
    starting(): void;
    styleAboutToChange(): void;
    styleChanged(newStyle: DzStyle): void;
    verboseMessage(message: string, category: string): void;
    warningMessage(message: string, category: string): void;
    debugMsg(message: string): void;
    warningMsg(message: string): void;
}

/**
 * Application Settings are used to store and retrieve settings that persist from one execution of the application to the next. On Windows, the settings are saved in the registry. On Mac, these settings are saved via Mac preference plist files. You can create an instance of this class any time you need to read or write persistent settings. This class is a replacement for DzAppSettingsMgr as it is easier and safer to use. Since each instance is separate, the current path of one instance will not affect the rest of the application. It is also not necessary to call popPath () to put this class back into its previous state.
 */
declare class DzAppSettings {
    containsValue(key: string): boolean;
    getBoolValue(key: string, def: boolean): boolean;
    getColorValue(key: string, def: { r: number, g: number, b: number, a: number }): { r: number, g: number, b: number, a: number };
    getFloatColorValue(key: string, def: DzFloatColor): DzFloatColor;
    getFloatValue(key: string, def: number): number;
    getIntValue(key: string, def: number): number;
    getStringValue(key: string, def: string): string;
    popPath(): void;
    pushPath(path: string): void;
    removeKey(key: string): boolean;
    removeValue(key: string): boolean;
    setBoolValue(key: string, setting: boolean): boolean;
    setColorValue(key: string, setting: { r: number, g: number, b: number, a: number }): boolean;
    setFloatColorValue(key: string, setting: DzFloatColor): boolean;
    setFloatValue(key: string, setting: number): boolean;
    setIntValue(key: string, setting: number): boolean;
    setStringValue(key: string, setting: string): boolean;
}

/**
 * An array is a data type that allows you to work with a list of elements. These elements can be any Object or QObject derived object. Multi-dimensional arrays are achieved by using array elements that are arrays themselves. Array Creation Arrays can be constructed using array literals, or by using the new operator. They can be extended dynamically by simply creating elements at non-existent index positions. Example: Array literal Example: Array literal Example: Using the new operator, initialized with a size, but with undefined elements Example: Using the new operator, defining all elements Example: Multi-Dimensional, dynamically extended Array Access Array elements are accessed by their names. Names can be integers or strings. As integers, element names are zero-based, meaning the first element is at 0, the second element is at 1 and so on. As strings, elements can act as normal properties, and can be accessed by using the square bracket operator ([]) or by directly dereferencing the Array object and specifying the property name (.name). These two accessor types can be mixed freely. Example: Integer access Example: Multi-Dimensional, integer access Example: String access, using the square bracket operator Example: String access, dereferencing the Array , specifying properties Array Iteration An array can be iterated over by using a for or for...in loop. Example: Iteration of element names as integers, using the for control statement Example: Iteration of element names as strings, using the for...in control statement. Todo Investigate whether there is a (Qt) bug in the return value of reverse, sort and slice; reference vs. copy.
 */
declare class Array {
    length(): number;

    isArray(obj: any): boolean;
    concat(element1: any, ...args: any[]): any[];
    every(callbackfn: Function, thisArg: any): boolean;
    filter(callbackfn: Function, thisArg: any): any[];
    forEach(callbackfn: Function, thisArg: any): void;
    indexOf(searchElement: any, fromIndex: number): number;
    join(separator: string, arg1: ”): string;
    lastIndexOf(searchElement: any, fromIndex: number): number;
    map(callbackfn: Function, thisArg: any): any[];
    pop(): any;
    push(element1: any, ...args: any[]): number;
    reduce(callbackfn: Function, initialValue: any): any;
    reduceRight(callbackfn: Function, initialValue: any): any;
    reverse(): any[];
    shift(): any;
    slice(startIndex: number, endIndex: number): any[];
    some(callbackfn: Function, thisArg: any): boolean;
    sort(comparisonFunction: Function): any[];
    splice(startIndex: number, deleteCount: number, ...args: any[]): any[];
    toLocaleString(): string;
    toString(): string;
    unshift(element1: any, ...args: any[]): number;
    find(element: any): number;
    pushIfNotExists(element1: any, ...args: any[]): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzArrayHelper {
    addToArray(list: any[], value: any): any[];
    isInArray(list: any[], value: any): number;
    isInArrayByName(list: any[], obj: any): number;
}

/**
 * An “Asset” serves as an abstraction between the presentation of a content file and the actual file that resides on disk; it is a “container” for information about a content file. At a minimum, an asset contains a reference to the relative path and filename of a file. Metadata When the Content Management System ( CMS ) is active, an asset provides an interface to its metadata within the content database. This metadata includes information such as what type of asset it is, what it is used for, what it is compatible with, which category(ies) it is presented to the user in, etc. Conceptually, each asset belongs to exactly one “Product”. By default, and until/unless modified, all newly created assets are assigned to the “LOCAL USER” product. An asset is uniquely identified within a product by the combination of its relative path and filename. While any number of products can reference a file with the same relative path and filename combination, each product's concept of that combination is unique (even if their metadata is identical). The metadata for a given asset is divided into 2 distinct types; that which is owned and/or maintained by the vendor (the originating source), and that which is owned and/or maintained by the end-user. Unless the metadata component (e.g., userKeywords, userNotes, etc), the product (e.g., “LOCAL USER”), or the store (e.g., “LOCAL USER”) indicate “user” in their name, any assumption (if there is to be one) about which type the data is should be that which is owned and/or maintained by the vendor. The metadata for an asset that is “installed” and which belongs to a product associated with a “Store” (source) other than the “LOCAL USER” store is owned by the vendor. Conversely, the metadata for an asset that is created by the user and/or belongs to a product associated with the “LOCAL USER” store is owned by the user. The exceptions to this are those attributes which integrate “user” into their name; which in fact always belong to the user. The significance of the distinction between the 2 types of metadata comes down to how the data is handled during an update and whether or not an effort is made to preserve it. Metadata that is owned and/or maintained by the vendor can be summarily purged during an update. This provides a vendor with the means to clean up all potential prior versions of the metadata without being faced with complex bookkeeping tasks. See Also: DzAssetMgr DzProductAssetContainer DzContentMgr
 */
declare class DzAsset {
    assetID(): any;
    assetName: string;
    audience: number;
    categories: any[];
    companionIsScript: boolean;
    companionPath: string;
    compatibilities: any[];
    compatibilityBase: string;
    contentType: string;
    dateCreated: Date;
    dateLastModified: Date;
    description: string;
    displayName: string;
    groupId: number;
    hasCloudMetadata: boolean;
    hasCompanion: boolean;
    hasCompanionScript: boolean;
    hidden: boolean;
    icon: Pixmap;
    isCloudInstallable: boolean;
    isCloudInstalled: boolean;
    isCloudOwned: boolean;
    isInstalled: boolean;
    isMetadataValid: boolean;
    isNative: boolean;
    isScript: boolean;
    isSymLink: boolean;
    isVendor: boolean;
    needsCloudInstall: boolean;
    needsCloudUpdate: boolean;
    notes: string;
    originalFilename: string;
    originalPath: string;
    productGUID: string;
    productID: string;
    productName: string;
    productPath: string;
    smallIcon: Pixmap;
    storeID: string;
    symLinkPath: string;
    url: string;
    urlEncoded: string;
    userCategories: any[];
    userCompatibilities: any[];
    userKeywords: any[];
    vendorCategories: any[];
    vendorCompatibilities: any[];
    vendorKeywords: any[];

    addCompatibilities(bases: any[], create: boolean): void;
    addToCategories(categories: any[], create: boolean): void;
    clearGroup(): void;
    forceImageReload(): void;
    getAsLocalFile(): string;
    getBaseExtension(): string;
    getDSLinkExtension(): string;
    getDSLinkText(): string;
    getOwner(): DzAbstractAssetContainer;
    getProduct(): DzProductAssetContainer;
    getRelativeFilePath(): string;
    isGroup(id: number): boolean;
    loadDefaultIcon(delayLoad: boolean): boolean;
    readLinkData(linkPath: string): any;
    removeCompatibilities(bases: any[], isVender: boolean): void;
    removeFromCategories(categories: any[], isVender: boolean): void;
    rename(name: string): boolean;
    saveDSLink(linkSavePath: string): boolean;
    setIgnoreExists(onOff: boolean): void;
    toUri(): DzUri;
    updateFromMetadata(guid: string): boolean;

    // SIGNALS
    assetImageChanged(asset: DzAsset): void;
}

/**
 * An asset save filter for saving a file in the DSON format.
 */
declare class DzAssetFileOutFilter {
}

/**
 * Save filter classes save out a subset of scene settings such as poses, light sets, camera sets, etc. in the DSON format. See Also: DzAssetIOMgr Samples: Save Filters
 */
declare class DzAssetIOFilter {
    doSave(filename: string, startingDir: string): DzError;
    doSave(options: DzFileIOSettings, filename: string, startingDir: string): DzError;
    getAssetDefinitionUri(base: DzBase): DzUri;
    getAssetInstanceUri(base: DzBase): DzUri;
    getCompatiblityBase(): string;
    getContentType(): string;
    getDescription(): string;
    getDoSavePath(): string;
    getLoadSavePath(): string;
    getSettingsPath(): string;
    getStandardSaveRelativePath(): string;
    isSupportAssetFilter(): boolean;
    setLoadSavePath(path: string): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzAssetIOFilterAction {
}

/**
 * Responsible for the management of the filters that load/save assets in the native DAZ Scene Object Notation (DSON) format. There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getAssetIOMgr (). See Also: Global :: App Samples: Save Filters
 */
declare class DzAssetIOMgr {
    currentSaveFilter(): DzAssetIOFilter;
    findAssetFilterIndex(className: string): number;
    findFilter(className: string): number;
    findObjectInstance(uri: DzUri): QObject;
    getAssetFilter(i: number): DzAssetIOFilter;
    getAssetFilterName(i: number): string;
    getFilter(i: number): DzAssetIOFilter;
    getFilterName(i: number): string;
    getNumAssetFilters(): number;
    getNumFilters(): number;
    isReading(): boolean;
    isReadingOrWriting(): boolean;
    isWriting(): boolean;
    doLoad(filename: string, method: DzOpenMethod, filter: DzFileLoadFilter): DzError;
    doSave(filterIndex: number): DzError;
    doSaveWithOptions(filter: DzAssetIOFilter, options: DzFileIOSettings, saveOnly: boolean, filename: string, startingDir: string, category: string): DzError;
    doSceneSaveAs(): DzError;
    getCurrentAssetContributor(): DzAuthor;
    getCurrentAssetId(): string;
    getCurrentAssetRevision(): DzVersion;
    getCurrentAssetType(): string;
    getCurrentFileInfo(): any;
    getCurrentFilename(): string;
    getCurrentFileVersion(): DzVersion;
    getDefaultDSONAssetCachePath(): string;
    getDSONAssetCachePath(): string;
    getFileAssetContributor(filename: string): DzAuthor;
    getFileAssetType(filename: string): string;
    getFileInfo(filename: string): any;
    getFileVersion(filename: string): DzVersion;
    getLoadPath(): string;
    getSavePath(): string;
    loadFromUri(fileUri: DzUri, method: DzOpenMethod, filter: DzFileLoadFilter): DzError;
    setDSONAssetCachePath(cacheFullPath: string): void;

    // SIGNALS
    assetImported(): void;
    assetImportStarting(): void;
    assetLoadError(filename: string): void;
    assetLoadFinished(filename: string): void;
    assetLoadStarted(filename: string): void;
    assetSaved(): void;
    assetSaveError(filename: string): void;
    assetSaveFinished(filename: string): void;
    assetSaveStarted(filename: string): void;
}

/**
 * Responsible for the management of database records associated with “content” (digital assets). There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getAssetMgr (). See Also: Global :: App DzAsset DzAbstractAssetContainer DzTopLevelAssetContainer DzProductHolderContainer DzProductAssetContainer DzCategoryAssetContainer DzCompatibilityBaseAssetContainer DzSearchContainer DzContentMgr Samples: Metadata
 */
declare class DzAssetMgr {
    captureSceneAssetPathsList(node: DzNode, options: any): any[];
    captureSceneAssetPathsList(options: any): any[];
    escapeSearchTerm(searchTerm: string): string;
    fileKeyForFilename(relativePath: string): string;
    findCommonBaseCategoryPath(categoryPaths: any[], flatten: boolean): string;
    getAssetUriForNode(node: DzNode): string;
    getCategoriesID(): string;
    getCompatibilityBasePathForNode(node: DzNode): string;
    getCompatibilityBasesID(): string;
    getDAZ3DStoreID(): number;
    getImportDirID(): string;
    getPoserDirID(): string;
    getPoserVirtualDirID(): any[];
    getProductName(name: string, choices: any[], allowEmpty: boolean): string;
    getProductsForFiles(filenames: any[]): any;
    getProductsID(): string;
    getRealPathCasing(path: string, search: string): string;
    getRelativeProductMetafilePath(store: string, token: string, title: string, extension: string): string;
    getSpecialPoserFolders(): any[];
    getStudioDirID(): string;
    getStudioExcludes(): any[];
    getStudioVirtualDirID(): any[];
    normalizePath(type: string, relative: boolean): string;
    saveUserDBData(dirPath: string, filePrefix: string): DzError;
    setCompatibilityBaseID(uri: string, id: number, markAsVendor: boolean): boolean;
    setCompatibilityBasePath(uri: string, compatibilityBasePath: string, markAsVendor: boolean, create: boolean): boolean;
    setFileMetadata(filepath: string, contentType: string, compatibleWith: string, category: string, assetNode: DzNode, compatibilityBase: string): void;
    buildMinimumProductSetForFiles(filenames: any[], products: any[]): any;
    buildMinimumProductSetForFiles(filenames: any[]): any;
    canStartAndStopCMS(): boolean;
    checkforNewMetadataScripts(): void;
    clearAllGroupIDs(notify: boolean): void;
    clearDBMetaFileQueue(): void;
    createCategoryPaths(paths: string, settingsName: string): void;
    createCompatibilityBase(base: string): number;
    createProduct(name: string, storeID: string, token: string): DzProductAssetContainer;
    createProductFromAssets(assets: any[], name: string): DzProductAssetContainer;
    createProductFromContainer(container: DzAbstractAssetContainer, name: string): DzProductAssetContainer;
    createStore(storeID: string, token: string, url: string): boolean;
    createSubContainer(parentContainer: DzAbstractAssetContainer, name: string, settingsName: string): DzAbstractAssetContainer;
    createType(type: string, defaultOpen: boolean): number;
    emitCategoryChanged(idPath: any[]): void;
    findAssetPathFromShortFilename(fileName: string): string;
    findAssetsForFile(relativePath: string, userFacing: boolean, installed: boolean): any[];
    findAudienceID(audience: string): number;
    findCategoryID(categoryPath: string, isVendor: boolean, create: boolean): number;
    findCompatibilityBaseID(base: string, create: boolean): number;
    findProductByGuid(guid: string): DzProductAssetContainer;
    findProductByStoreToken(storeID: string, token: string): DzProductAssetContainer;
    findProductsByName(name: string): any[];
    findProductsForFile(relativePath: string): any[];
    findTypeID(type: string, create: boolean, defaultOpen: boolean): number;
    getAudience(id: number): string;
    getAudiences(): any[];
    getCategories(): DzCategoryAssetContainer;
    getCategoryData(includeHeader: boolean, dataType: MetadataTypes): any[];
    getCategoryPath(id: number): string;
    getCMSBasePath(create: boolean): string;
    getCMSOptions(): any;
    getCMSPort(): number;
    getCompatibilityBase(id: number): string;
    getCompatibilityBaseData(includeHeader: boolean, baseType: CompatibilityBaseTypes, dataType: MetadataTypes): any[];
    getCompatibilityBases(includeFilters: boolean): DzCompatibilityBaseAssetContainer;
    getContainerName(title: string, placeHolder: string, settingsName: string): string;
    getContentDirs(): DzTopLevelAssetContainer;
    getDatabaseDsn(): string;
    getDatabaseFilePath(): string;
    getDBMetaFileQueue(): any[];
    getDefaultCategoryPaths(prefix: string, append: boolean): any[];
    getDefaultCMSBasePath(): string;
    getDefaultCMSPort(): number;
    getFirstCategory(assetPath: string, preferredCategory: string, installed: boolean): string;
    getGroupNewProductsAsNew(): boolean;
    getImportDirs(): DzTopLevelAssetContainer;
    getMaxFileSearchResultSize(): number;
    getNumMaxItemsPerPage(): number;
    getPoserDirs(): DzTopLevelAssetContainer;
    getProducts(): DzTopLevelAssetContainer;
    getRelativePaths(absolutePath: string, useImportFolders: boolean): any[];
    getRootCategoryStrings(): any[];
    getShowHiddenVendorCategorization(): boolean;
    getStoresIDs(): any[];
    getStoreToken(storeID: string): string;
    getStoreUrl(storeID: string): string;
    getType(id: number): string;
    getTypeForContentFile(path: string): string;
    getTypeForNode(node: DzNode): string;
    getTypes(): any[];
    getUniqueChildCategoryName(categoryPath: string, name: string): string;
    haveDatabase(): boolean;
    importMetadataFiles(absoluteProductPaths: any[], runSilent: boolean, markAsVendor: boolean): any[];
    installMissingAssets(filenames: any[], noPrompt: boolean, productMsg: string, unknownMsg: string): any;
    isClothingType(type: string): boolean;
    isConnectedToCMS(): boolean;
    isFigureType(type: string): boolean;
    isFollowingType(type: string): boolean;
    isHairType(type: string): boolean;
    isNeedsBaseFigureType(type: string): boolean;
    isPresetForFigureType(type: string): boolean;
    isPresetType(type: string): boolean;
    isPropType(type: string): boolean;
    isReplaceableType(type: string): boolean;
    isResettingDatabase(): boolean;
    isSynchronizing(): boolean;
    markCategoriesChanged(): void;
    markProductsChanged(): void;
    processDBMetaFile(productRelativePath: string, runSilent: boolean, markAsVendor: boolean, groupAsNew: boolean): any[];
    processDBMetaFileNoEmit(productRelativePath: string, runSilent: boolean, markAsVendor: boolean, groupAsNew: boolean): any[];
    processDBMetaFileQueue(): void;
    queueDBMetaFile(productRelativePath: string): void;
    refreshCategoryRoots(): void;
    refreshStores(): void;
    refreshTypes(): void;
    reimportDBMetaFiles(): void;
    removeOrphanedAssetReferences(list: any[]): void;
    removeStore(storeID: string): boolean;
    resetDatabase(): void;
    scanFiles(options: SearchOptions, assignToGroup: boolean, addToCategory: boolean, onlyNewToCategory: boolean): void;
    searchFiles(filename: string, options: SearchOptions): DzSearchContainer;
    searchForAssetAddOns(asset: DzAsset, filterText: string, categories: any[], sorting: SortType): DzSearchContainer;
    searchForAssets(filterText: string, categories: any[], compatibilityBases: any[], contentTypes: any[], sorting: SortType): DzSearchContainer;
    searchForAssetsByKeywords(keywords: string, options: SearchOptions, sorting: SortType): DzSearchContainer;
    searchForAssetsInCategory(categoryPath: string, userFacing: boolean, installed: boolean): DzSearchContainer;
    searchForAssetTargets(asset: DzAsset, filterText: string, categories: any[], sorting: SortType): DzSearchContainer;
    searchForProductAssets(product: DzProductAssetContainer, filterText: string, categories: any[], compatibilityBases: any[], contentTypes: any[], sorting: SortType): DzSearchContainer;
    searchForProducts(filterText: string, categories: any[], compatibilityBases: any[], contentTypes: any[], installStateFlags: ProductInstallStates, sorting: SortType): DzProductHolderContainer;
    selectCategoryPaths(multiSelect: boolean, startWith: any[], title: string, settingsName: string): any[];
    selectCompatibilityBasePaths(showFilters: boolean, multiSelect: boolean, startWith: any[], title: string, settingsName: string): any[];
    setCMSOptions(clusterDirectory: string, port: number): void;
    setGroupNewProductsAsNew(onOff: boolean): void;
    setMaxFileSearchResultSize(maxNum: number): void;
    setMaxItemsPerPage(maxNum: number): void;
    setProductGroupIDs(guids: any[], groupId: number, groupProduct: boolean, groupFiles: boolean): void;
    setShowAssetToolTip(onOff: boolean): void;
    setShowExtensions(onOff: boolean): void;
    setShowHiddenVendorCategorization(shown: boolean): void;
    setShowLargeIcons(onOff: boolean): void;
    showAssetToolTip(): boolean;
    showDatabaseEditor(assetContainer: DzAbstractAssetContainer): boolean;
    showExtensions(): boolean;
    showLargeIcons(): boolean;
    showMoreProductInfo(product: DzProductAssetContainer): void;
    startCMS(): void;
    stopAllSearches(): void;
    stopCMS(mode: StopModeCMS, wait: boolean, timeout: number): void;
    stopFileScan(): void;
    stopFileSearch(): void;
    stopSearchForAssetAddOns(): void;
    stopSearchForAssets(): void;
    stopSearchForAssetTargets(): void;
    stopSearchForProducts(): void;
    updateCategoryContainers(): void;
    updateContentContainers(): void;
    updateFolderBasedContainers(): void;
    updateImportContainers(): void;
    updatePoserContainers(): void;
    updateProductContainers(): void;
    vacuumDatabase(): boolean;

    // SIGNALS
    basePathsChanged(): void;
    categoryUpdate(idPath: any[]): void;
    cmsDSNChanged(): void;
    cmsStarted(): void;
    cmsStopped(): void;
    compatibilityBaseListChanged(): void;
    containerUpdate(idPath: any[]): void;
    groupNewProductsAsNewChanged(): void;
    itemsPerPageChanged(newPerPage: number): void;
    maxFileSearchResultSizeChanged(maxFileSearchResultSize: number): void;
    productCreated(guid: string): void;
    showAssetToolTipChanged(): void;
    showExtensionsChanged(): void;
    showHiddenVendorCategorizationChanged(): void;
    showLargeIconsChanged(): void;
    storeListChanged(): void;
    typeListChanged(): void;
    uiAboutToSearch(sender: QObject, text: string, categories: any[], compatibilityBases: any[], contentTypes: any[]): void;
}

/**
 * This class is implemented by platform specific audioclip classes, winaudioclip_dz and macaudioclip_dz . See Also: DzScene :: getAudio (), DzScene :: setAudio (), DzAudioImporter , DzMultiMediaMgr :: importAudioClip ()
 */
declare class DzAudioClip {
    currentPosition(): number;
    filename: string;
    length: number;
    rate: number;

    openFile(filename: string): DzError;
    pause(): void;
    play(): void;
    reset(): void;
}

/**
 * See Also: DzMultiMediaMgr
 */
declare class DzAudioImporter {
    getDescription(): string;
    getExtension(): string;
    loadAudio(filename: string, clip: DzAudioClip, options: DzFileIOSettings): DzError;
    loadAudio(filename: string, clip: DzAudioClip): DzError;
    recognize(filename: string): boolean;
}

/**
 * This class does not provide access to any Daz 3D user account information which could be considered an invasion of the user's privacy. This class does provide plugins and scripts with an ability to check if a user has authenticated (logged in to) a Daz 3D account, to prompt a user to authenticate (login to) their Daz 3D account, to obtain a token that uniquely and anonymously identifies the current/last account authenticated, and to logout of an account that is currently logged in. There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getAuthenticationMgr (). See Also: Global :: App Sample: Retrieve User Token
 */
declare class DzAuthenticationMgr {
    authenticateUser(): boolean;
    getUserToken(): string;
    isAuthenticated(): boolean;
    isLoggingIn(): boolean;
    logout(): void;

    // SIGNALS
    beginLogin(): void;
    beginLogout(): void;
    currentAccountChanged(): void;
    loggedIn(): void;
    loggedOut(): void;
}

/**
 * DzAuthor is used to access authorship data for native files, and the current instance of the application. See Also: DzApp :: getCurrentAuthor () DzScript :: getAuthor () DzScriptContext :: getScriptAuthor () Global :: getScriptAuthor ()
 */
declare class DzAuthor {
    email(): string;
    name: string;
    url: string;
    valid: string;
}

/**
 * This class encapsulates a 2D image and the parameters for drawing the image as a backdrop for the scene. An instance of this class only contributes to the scene if it is set as the current backdrop for the scene. See Also: DzScene :: setBackdrop () DzScene :: getBackdrop ()
 */
declare class DzBackdrop {
    backgroundColor(): { r: number, g: number, b: number, a: number };
    flipHorizontal: boolean;
    flipVertical: boolean;
    rotation: Rotation;
    visible: boolean;
    visibleInRender: boolean;

    adjustRenderAspectRatioToMatchTexture(): void;
    adjustRenderDimensionsToMatchTexture(): void;
    clear(): void;
    getBackgroundColorControl(): DzColorProperty;
    getHorizontalFlipControl(): DzBoolProperty;
    getMaterial(): DzMaterial;
    getRotationControl(): DzEnumProperty;
    getTexture(): DzTexture;
    getVerticalFlipControl(): DzBoolProperty;
    getVisibleControl(): DzBoolProperty;
    getVisibleInRenderControl(): DzBoolProperty;
    setTexture(img: DzTexture): void;
    showOptions(parent: QWidget): void;

    // SIGNALS
    backgroundColorChanged(): void;
    drawnDataChanged(): void;
    visiblityChanged(): void;
}

/**
 * Derived from QObject , this base class allows for the use of the signals-slots architecture provided by the Qt framework, within the Daz Studio API . A considerable portion of classes in the Daz Studio API derive from this class.
 */
declare class DzBase {
    makePersistent(): void;

    // SIGNALS
    nameChanged(name: string): void;
}

/**
 * This is the basic camera implementation for DAZ Studio. It supplies commonly-used features like focal length adjustment and depth of field alteration.
 */
declare class DzBasicCamera {
    currentViewHeight(): number;
    currentViewWidth: number;
    depthOfField: boolean;
    farDofPlane: number;
    fStop: number;
    isPerspective: boolean;
    nearDofPlane: number;
    useActiveViewport: boolean;

    applyDimensionsPreset(preset: string): boolean;
    cursorToRay(x: number, y: number): DzVec3;
    cursorToScene(x: number, y: number, z: number): DzVec3;
    getApertureBladeRotationAngleControl(): DzFloatProperty;
    getApertureNumBladesControl(): DzIntProperty;
    getAspectRatioControl(): DzFloat2Property;
    getConstrainProportionsControl(): DzBoolProperty;
    getDepthOfFieldControl(): DzBoolProperty;
    getDimensionPresetControl(): DzStringProperty;
    getDimensionsPreset(preset: string, settings: DzSettings): boolean;
    getDisplayPersistenceControl(): DzBoolProperty;
    getDofOverlayColorControl(): DzColorProperty;
    getDofOverlayOpacityControl(): DzFloatProperty;
    getDofPlaneColorControl(): DzColorProperty;
    getDofPlaneVisibilityControl(): DzBoolProperty;
    getFarDofPlaneVisibilityControl(): DzBoolProperty;
    getFocalDistanceControl(): DzFloatProperty;
    getFocalLengthControl(): DzFloatProperty;
    getFocalPointScaleControl(): DzFloatProperty;
    getFovColorControl(): DzColorProperty;
    getFovLengthControl(): DzFloatProperty;
    getFovOpacityControl(): DzFloatProperty;
    getFrameWidthControl(): DzFloatProperty;
    getFStopControl(): DzFloatProperty;
    getHeadlampIntensityControl(): DzFloatProperty;
    getHeadlampModeControl(): DzEnumProperty;
    getLensDistortionK1Control(): DzFloatProperty;
    getLensDistortionK2Control(): DzFloatProperty;
    getLensDistortionK3Control(): DzFloatProperty;
    getLensDistortionK4Control(): DzFloatProperty;
    getLensDistortionK5Control(): DzFloatProperty;
    getLensDistortionScaleControl(): DzFloatProperty;
    getLensDistortionTypeControl(): DzEnumProperty;
    getLensMaximumFovControl(): DzFloatProperty;
    getLensRadialBiasControl(): DzFloatProperty;
    getLensShiftXControl(): DzFloatProperty;
    getLensShiftYControl(): DzFloatProperty;
    getLensStereoOffsetControl(): DzFloatProperty;
    getLensThicknessControl(): DzFloatProperty;
    getNearDofPlaneVisibilityControl(): DzBoolProperty;
    getPerspectiveControl(): DzBoolProperty;
    getPixelSizeControl(): DzInt2Property;
    getSightLineOpacityControl(): DzFloatProperty;
    getUseLocalDimensionsControl(): DzBoolProperty;
    getXHeadlampOffsetControl(): DzFloatProperty;
    getYHeadlampOffsetControl(): DzFloatProperty;
    getZHeadlampOffsetControl(): DzFloatProperty;
    isAtDefaultSceneCameraValues(): boolean;
    isDefaultSceneCamera(): boolean;
    setIsDefaultSceneCamera(yesNo: boolean): void;
    setType(type: CameraType): void;
    getFrameWidthChannel(): DzFloatProperty;
    getFocalLengthChannel(): DzFloatProperty;
    getDepthOfFieldChannel(): DzBoolProperty;
    getFocalDistChannel(): DzFloatProperty;
    getFStopChannel(): DzFloatProperty;
    getDisplayPersistenceChannel(): DzBoolProperty;
    getSightLineOpacityChannel(): DzFloatProperty;
    getFocalPointScaleChannel(): DzFloatProperty;
    getFovColorChannel(): DzColorProperty;
    getFovOpacityChannel(): DzFloatProperty;
    getFovLengthChannel(): DzFloatProperty;
    getDofVisibilityChannel(): DzBoolProperty;
    getDofColorChannel(): DzColorProperty;
    getDofOverlayColorChannel(): DzColorProperty;
    getDofOverlayOpacityChannel(): DzFloatProperty;
    getNearDofVisibilityChannel(): DzBoolProperty;
    getFarDofVisibilityChannel(): DzBoolProperty;

    // SIGNALS
    depthOfFieldChanged(): void;
    fStopChanged(range: DzTimeRange): void;
}

/**
 * The buttons provided by the dialog are: 'What's This', 'Apply', 'Accept', and 'Cancel'. Custom buttons can also be added to the set of default buttons by calling addButton (). All buttons but the 'Accept' button can be hidden or shown. By default, the 'Apply' button is the only hidden button. The text on the default buttons can be customized. The dialog has a vertical box layout above the horizontal set of buttons. Widgets and sub-layouts can be added to this layout using addWidget () and addLayout (). See Also: Sample: Simple Input Dialog Sample: Simple Image Dialog Sample: Action Accelerators Sample: Version Conversion
 */
declare class DzBasicDialog {
    addButton(btn: DzButton, index: number): void;
    addLayout(layout: DzLayout, stretch: number): void;
    addSpacing(spacing: number): void;
    addStretch(stretch: number): void;
    addWidget(child: DzWidget, stretch: number, alignment: AlignmentFlags): void;
    insertLayout(index: number, layout: DzLayout, stretch: number): void;
    insertWidget(index: number, child: DzWidget, stretch: number, alignment: AlignmentFlags): void;
    setAcceptButtonAsDefault(): void;
    setAcceptButtonEnabled(onOff: boolean): void;
    setAcceptButtonText(text: string): void;
    setApplyButtonAsDefault(): void;
    setApplyButtonEnabled(onOff: boolean): void;
    setApplyButtonText(text: string): void;
    setCancelButtonAsDefault(): void;
    setCancelButtonEnabled(onOff: boolean): void;
    setCancelButtonText(text: string): void;
    setDefaultButton(btn: DzButton): void;
    setHelpButtonAsDefault(): void;
    setHelpButtonEnabled(onOff: boolean): void;
    showAcceptButton(onOff: boolean): void;
    showApplyButton(onOff: boolean): void;
    showCancelButton(onOff: boolean): void;
    showHelpButton(onOff: boolean): void;
    enableApplyButton(onOff: boolean): void;
    enableCancelButton(onOff: boolean): void;
    enableHelpButton(onOff: boolean): void;

    // SIGNALS
    applyClicked(): void;
}

/**
 * This specialized DzNode subclass adds follow bone, and mesh-binding functionality to a node. All bones are assumed to be in the hierarchy of a DzSkeleton , and will not function properly if their parent is not a skeleton or another bone. The concept of a follow bone allows the bones of one skeleton (figure) to follow another skeleton (figure). This following does not reproduce transforms from one bone to another, but tries to align center (origin) and end points so that the following bone points in the same direction as the bone it is following. Typically, this is controlled at the skeleton level.
 */
declare class DzBone {
    getBoneLocalScale(tm: number): DzMatrix3;
    getFollowBone(): DzBone;
    getFollowMode(): number;

    // SIGNALS
    followBoneChanged(newFollowBone: DzBone): void;
}

/**
 * See Also: DzSkinBinding
 */
declare class DzBoneBinding {
}

/**
 * ECMAScript provides a Boolean data type that can have one of two primitive values, true or false. In general, creating objects of this type is not recommended since the behavior will probably not be what you would expect. Instead, assign the literal value true or false as required. Any expression can be evaluated in a boolean context (e.g. in logical operations, such as conditionals). If the expression's value is 0, null, false , NaN, undefined or an empty String , the expression is false ; otherwise the expression is true . Example: Creating boolean values using the true/false constants Example: Creating a boolean values using the evaluation of expressions
 */
declare class Boolean {
    toString(): string;
    valueOf(): number;
}

/**
 * This class provides an animatable boolean property that is stored and can be accessed as an integer property. The integer value 0 is false, any other integer value is true.
 */
declare class DzBoolProperty {
    getBoolValue(): boolean;
    getDefaultBoolValue(): boolean;
    setBoolValue(value: boolean): void;
    setDefaultBoolValue(val: boolean): void;
}

/**
 * Represents a three dimensional box by storing two three dimensional floating point vectors; an upper and lower corner for this box.
 */
declare class DzBox3 {
    max(): DzVec3;
    maxX: number;
    maxY: number;
    maxZ: number;
    min: DzVec3;
    minX: number;
    minY: number;
    minZ: number;

    closestPoint(point: DzVec3): DzVec3;
    containsPoint(point: DzVec3): boolean;
    getCenter(): DzVec3;
    getIntersection(ray: DzLine3): any;
    getSize(): number;
    getTransformedBox(matrix: DzMatrix3): DzBox3;
    include(vec: DzVec3): void;
    include(box: DzBox3): void;
    isValid(): boolean;
    testIntersection(ray: DzLine3, tolerance: number): boolean;
    toString(): string;
    translate(vec: DzVec3): void;
}

/**
 * A layout that manages child items in a horizontal or vertical box.
 */
declare class DzBoxLayout {
    direction(): Direction;

    addLayout(item: DzLayout, stretch: number): void;
    addSpacing(size: number): void;
    addStretch(stretch: number): void;
    addStrut(size: number): void;
    addWidget(item: DzWidget, stretch: number): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzBrickMaterial {
    convertDefaultMaterial(mat: DzDefaultMaterial): DzBrickMaterial;
    convertUberIrayMaterial(mat: DzMaterial): DzBrickMaterial;
    addBrick(brick: DzShaderBrick): number;
    allowsAutoBake(): boolean;
    applyToScene(): void;
    deleteAllBricks(): void;
    deleteBrick(id: number): void;
    deleteBrick(brick: DzShaderBrick): void;
    endEditMode(): void;
    getBrick(id: number): DzShaderBrick;
    getBrickIDs(): any[];
    getBrickSet(i: number): DzBrickSet;
    getBrickUserName(): string;
    getExtension(): string;
    getNumBrickSets(): number;
    invalidateSets(): void;
    isInEditMode(): boolean;
    setBrickUserName(name: string): void;
    setMaterialName(name: string): void;
    setNeedsPtexParams(onoff: boolean): void;
    setNeedsTangentSpaceParams(onoff: boolean): void;
    startEditMode(): void;
    updateIdentifierOnSetInvalidate(onOff: boolean): void;
    usesLocalShaderSpace(): boolean;

    // SIGNALS
    brickAdded(brick: DzShaderBrick): void;
    brickRemoved(brick: DzShaderBrick): void;
    generateFilesFinished(): void;
    generateFilesStarted(): void;
}

/**
 * This class holds a root brick and handles tracing that root brick through its children to form a RSL and/or MDL shader. A root brick is any brick that does not have a DzBrickSet :: ShaderType of NONE. See Also: DzShaderBrick
 */
declare class DzBrickSet {
    getFullShaderPath(): string;
    getShaderFile(): string;
    invalidateFiles(): void;
    sendForUpdate(): void;
}

/**
 * DzButton implements an abstract button base. Subclasses specify how to respond to user interaction, and how to present the button to the user. If you want to create a button, create a DzPushButton . DzPushButton provides both push and toggle buttons. The DzRadioButton and DzCheckBox classes provide only toggle buttons. The difference between down and on is, when a user clicks a [toggle] button to toggle it on, the button is first pressed and then released into the On state ( on is true , down is false ). When the user clicks it again (to toggle it off), the button is first pressed and then released to the Off state ( on and down are false ).
 */
declare class DzButton {
    autoRepeat(): boolean;
    autoRepeatDelay: number;
    autoRepeatInterval: number;
    checkable: boolean;
    checked: boolean;
    down: boolean;
    pixmap: Pixmap;
    text: string;
    toggleButton: boolean;
    exclusiveToggle: boolean;
    on: boolean;
    toggleState: ToggleState;
    toggleType: ToggleType;

    toggle(): void;

    // SIGNALS
    clicked(): void;
    pressed(): void;
    released(): void;
    stateChanged(state: number): void;
    toggled(onOff: boolean): void;
}

/**
 * Provides an abstract container that manages the states of DzButton instances placed within it - it does not provide a visual representation. See Also: DzGroupBox
 */
declare class DzButtonGroup {
    count(): number;
    exclusive: boolean;
    radioButtonExclusive: boolean;
    selected: number;

    addButton(button: DzButton): void;
    addButton(button: DzButton, id: number): void;
    button(id: number): DzButton;
    buttons(): any[];
    checkedButton(): DzButton;
    id(button: DzButton): number;
    insert(button: DzButton, id: number): number;
    removeButton(button: DzButton): void;
    remove(button: DzButton): void;

    // SIGNALS
    clicked(id: number): void;
    pressed(id: number): void;
    released(id: number): void;
}

/**
 * See Also: DzExportMgr :: findExporterByClassName () DzExportMgr :: findExporter ()
 */
declare class DzBvhExporter {
}

/**
 * See Also: DzImportMgr :: findImporterByClassName () DzImportMgr :: findImporter ()
 */
declare class DzBvhImporter {
}

/**
 * This is the script counterpart to the QByteArray type used in the C++ SDK. Attention: Inheritance will change to Object in a pending update.
 */
declare class ByteArray {
    length(): number;
    size: number;

    byteAt(index: number): number;
    charAt(index: number): string;
    convertToString(): string;
    convertToStringFromUtf16(): string;
    convertToStringFromUtf8(): string;
    fromBase64(base64: ByteArray): ByteArray;
    fromHex(hexEncoded: ByteArray): ByteArray;
    fromPercentEncoding(pctEncoded: ByteArray): ByteArray;
    toBase64(): ByteArray;
    toHex(): ByteArray;
    toPercentEncoding(exclude: ByteArray, include: ByteArray): ByteArray;
}

/**
 * Encapsulates an object that is used to execute a script when a signal that it is connected to is triggered. See Also: DzCallBackMgr :: createCallBack () DzCallBackMgr :: getCallBack ()
 */
declare class DzCallBack {
    addToGroup(group: string): void;
    clearConnection(): void;
    clearScriptFunction(): void;
    getArg(i: number): any;
    getArgCount(): number;
    getBlockedDuringSceneLoad(): boolean;
    getDeleteAfterExecution(): boolean;
    getDynamicProperty(name: string): any;
    getGroups(): any[];
    getProcessAsEvent(): boolean;
    getScript(): string;
    getSender(): QObject;
    isEvaluated(): boolean;
    removeFromGroup(group: string): void;
    setBlockedDuringSceneLoad(onOff: boolean): void;
    setConnection(sender: QObject, signal: string): boolean;
    setConnection(sender: QObject, signal: string, garbageCollect: boolean): boolean;
    setConnections(sender: QObject, signalList: any[], garbageCollect: boolean): number;
    setDeleteAfterExecution(onOff: boolean): void;
    setDynamicProperty(name: string, value: any): void;
    setProcessAsEvent(onOff: boolean): void;
    setScript(script: string, evaluate: boolean): void;
    setScriptFunction(functionRef: Function, thisObject: any): void;
    setScriptFunction(functionRef: Function): void;
}

/**
 * Responsible for the management of objects that are used to execute a script when a signal that the object is connected to is emitted. There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getCallBackMgr (). Example: Dynamically load a script. Example: Embed a script. Example: CallBack script (./support/CallBackExample/HelloWorld.dsa). “CallBack” is a global transient variable referring to the DzCallBack that executes the script. See Also: Global :: App Samples: Post-Load Callbacks
 */
declare class DzCallBackMgr {
    clearAllCallBacks(): void;
    createCallBack(name: string, script: string, evaluate: boolean): DzCallBack;
    createCallBack(name: string): DzCallBack;
    deleteCallBack(index: number): void;
    deleteCallBack(name: string): void;
    deleteCallBack(callBack: DzCallBack): void;
    deleteCallBackGroup(name: string): void;
    getCallBack(index: number): DzCallBack;
    getCallBack(name: string): DzCallBack;
    getCallBackIndex(name: string): number;
    getCallBackList(): any[];
    getGroup(name: string): any[];
    getNumCallBacks(): number;
    getSignalSignature(obj: QObject, signalName: string): any[];
}

/**
 * TODO: Add detailed description.
 */
declare class DzCamera {
    aspectHeight(): number;
    aspectRatio: number;
    aspectWidth: number;
    farClippingPlane: number;
    focalDistance: number;
    focalLength: number;
    frameWidth: number;
    headlightMode: HeadlightMode;
    headlightOffset: DzVec3;
    nearClippingPlane: number;
    pixelsHeight: number;
    pixelsWidth: number;
    proportionsConstrained: boolean;
    type: number;
    useLocalDimensions: boolean;

    aimAt(pos: DzVec3): void;
    frame(box: DzBox3, aspect: number): void;
    getFieldOfView(): number;
    getFocalPoint(): DzVec3;
    getHeadlight(): DzLight;
    isViewCamera(): boolean;
    reset(): void;
    shouldDoHeadLight(hasLights: boolean, isRender: boolean): boolean;
    updateDimensions(anchor: CameraDimension): void;

    // SIGNALS
    aspectHeightChanged(height: number): void;
    aspectRatioChanged(): void;
    aspectWidthChanged(width: number): void;
    dimensionsChanged(): void;
    focalDistanceChanged(range: DzTimeRange): void;
    focalLengthChanged(range: DzTimeRange): void;
    frameWidthChanged(size: number): void;
    headlightModeChanged(): void;
    headlightOffsetChanged(): void;
    pixelDimensionsChanged(): void;
    pixelsHeightChanged(height: number): void;
    pixelsWidthChanged(width: number): void;
    projectionChanged(): void;
    proportionsConstrainedChanged(yesNo: boolean): void;
    useLocalDimensionsChanged(yesNo: boolean): void;
}

/**
 * An asset save filter for saving a Camera(s) Preset in the DSON format. See Also: Sample: Save a Camera(s) Preset
 */
declare class DzCameraAssetFilter {
}

/**
 * A “Category” is described as a class or collection of entities regarded as having common traits and/or characteristics. Within a given class or collection of entities, certain traits and/or characteristics may be regarded as being shared by a smaller subset - i.e., a “Sub-Category.” Thus, categorization naturally supports a hierarchical structure. The “Category” container type serves to provide a means of working with “Assets” that share characteristics without the encumbrances imposed by moving the actual files they represent on disk - moving or renaming files on disk breaks the correlation between the file and the “Asset” that represents it. See Also: DzAssetMgr :: getCategories () DzAsset
 */
declare class DzCategoryAssetContainer {
    isVendor(): boolean;

    getAssetsInCategory(userFacing: boolean, installed: boolean): any[];
    getPath(): string;
    updateRow(): void;
}

/**
 * An asset save filter for saving a Character Preset in DSON format. See Also: Sample: Save a Character Preset
 */
declare class DzCharacterAssetFilter {
}

/**
 * DzRadioButton and DzCheckBox are both option buttons (e.g. they can be checked or unchecked). They differ in how the available choices are restricted. A DzCheckBox is used to define several choices that can all co-exist at the same time (e.g. “many of many”). While a DzRadioButton is used to provide several choices, where only one can be ultimately chosen (e.g. “one of many”). Example:
 */
declare class DzCheckBox {
    checked(): boolean;
    tristate: boolean;
}

/**
 * This is not a widget, but a helper for working with DzListView . Each DzCheckListItem represents a single item in a list view - add items to a list view by creating a new DzCheckListItem that is a child of the list view, or a child of another list view item in the list view.
 */
declare class DzCheckListItem {
    height(): number;
    on: boolean;
    state: ToggleState;
    triState: boolean;
    type: Type;
}

/**
 * TODO: Add detailed description.
 */
declare class DzCircle3 {
    center(): DzVec3;
    normal: DzVec3;
    radius: number;

    toString(): string;
}

/**
 * This is the script counterpart to the QColor type used in the C++ SDK. Attention: Inheritance will change to Object in a pending update.
 */
declare class Color {
    alpha(): number;
    blue: number;
    green: number;
    hue: number;
    name: string;
    red: number;
    rgb: number;
    saturation: number;
    value: number;

    dark(): { r: number, g: number, b: number, a: number };
    isValid(): boolean;
    light(): { r: number, g: number, b: number, a: number };
    setRgb(r: number, g: number, b: number, a: number): void;
    setRgb(r: number, g: number, b: number): void;
    setRgb(colorCode: number): void;
}

/**
 * A global static object available via the Global :: ColorDialog variable. This object provides functions to display an OS native color picker to the user - simply call the function as shown in the following example: Example - Have the user select a color : Other functions are provided for getting and setting the pre-set colors listed in the picker - see the rest of the documentation for details.
 */
declare class DzColorDialog {
    customColor(i: number): { r: number, g: number, b: number, a: number };
    customCount(): number;
    getColor(initial: { r: number, g: number, b: number, a: number }): { r: number, g: number, b: number, a: number };
    setCustomColor(i: number, c: { r: number, g: number, b: number, a: number }): void;
    setStandardColor(i: number, c: { r: number, g: number, b: number, a: number }): void;
}

/**
 * This class provides an animatable color property that is stored and can be accessed as an integer property. The integer value represents a color as a 32 bit rgba value with each byte representing a component with the range [0, 255].
 */
declare class DzColorProperty {
    animationBlendModeFromStr(str: string): AnimationBlendMode;
    animationBlendModeToStr(type: AnimationBlendMode): string;
    getAnimationBlendMode(): AnimationBlendMode;
    getColorValue(): { r: number, g: number, b: number, a: number };
    getColorValue(tm: number): { r: number, g: number, b: number, a: number };
    getDefaultColorValue(): { r: number, g: number, b: number, a: number };
    getKeyColorValue(i: number): { r: number, g: number, b: number, a: number };
    getRawColorValue(tm: number): { r: number, g: number, b: number, a: number };
    getRawColorValue(): { r: number, g: number, b: number, a: number };
    setAnimationBlendMode(mode: AnimationBlendMode): void;
    setColorValue(tm: number, val: { r: number, g: number, b: number, a: number }): void;
    setColorValue(val: { r: number, g: number, b: number, a: number }): void;
    setDefaultColorValue(val: { r: number, g: number, b: number, a: number }): void;
    setKeyColorValue(i: number, val: { r: number, g: number, b: number, a: number }): void;

    // SIGNALS
    animationBlendModeChanged(): void;
}

/**
 * Provides a control for displaying/selecting a color.
 */
declare class DzColorWgt {
    defaultFloatColorValue(): DzFloatColor;
    defaultValue: { r: number, g: number, b: number, a: number };
    displayAsInt: boolean;
    floatClamped: boolean;
    floatColorValue: DzFloatColor;
    floatMax: number;
    floatMin: number;
    indeterminate: boolean;
    isEditing: boolean;
    restorable: boolean;
    value: { r: number, g: number, b: number, a: number };

    // SIGNALS
    colorChanged(color: { r: number, g: number, b: number, a: number }): void;
    editEnd(): void;
    editStart(): void;
    floatColorChanged(color: DzFloatColor): void;
}

/**
 * Provides a means of presenting a list of options to the user in a way that takes up the minimum amount of screen space.
 */
declare class DzComboBox {
    count(): number;
    currentItem: number;
    currentText: string;
    insertPolicy: InsertPolicy;
    maxVisibleItems: number;
    minimumContentsLength: number;
    sizeAdjustPolicy: SizeAdjustPolicy;

    addItem(text: string, userData: string): void;
    addItems(texts: any[]): void;
    clear(): void;
    findData(data: string): number;
    findText(text: string): number;
    insertItem(index: number, text: string, userData: string): void;
    insertItems(index: number, list: any[]): void;
    insertSeparator(index: number): void;
    itemData(index: number): string;
    itemText(index: number): string;
    removeItem(index: number): void;
    setItemData(index: number, value: string): void;
    setItemText(index: number, text: string): void;
    insertItem(text: string): void;
    text(index: number): string;

    // SIGNALS
    activated(index: number): void;
    currentIndexChanged(index: number): void;
    highlighted(index: number): void;
    textChanged(text: string): void;
    activated(text: string): void;
    currentIndexChanged(text: string): void;
    highlighted(text: string): void;
}

/**
 * Provides a compound widget comprised of a line edit and a button that, when clicked, causes a menu to be displayed. Selecting one of the items in the popup menu causes the value of the editor to update with the text of the selected item by default. See Also: DzLineEdit DzPushButton DzPopupMenu
 */
declare class DzComboEdit {
    acceptableInput(): boolean;
    alignment: AlignmentFlags;
    appendDelimiter: string;
    cursorPosition: number;
    holdModifierAppend: boolean;
    inputMask: string;
    maxLength: number;
    menuSelectionIncludesPath: boolean;
    modified: boolean;
    placeholderText: string;
    readOnly: boolean;
    redoAvailable: boolean;
    showClearButton: boolean;
    submenuDelimiter: string;
    text: string;
    undoAvailable: boolean;
    usePathPopUp: boolean;

    addItem(item: string, validate: boolean): void;
    addItems(items: any[], validate: boolean): void;
    backspace(): void;
    clear(): void;
    clearText(): void;
    copy(): void;
    cursorBackward(mark: boolean, steps: number): void;
    cursorForward(mark: boolean, steps: number): void;
    cursorWordBackward(mark: boolean, steps: number): void;
    cursorWordForward(mark: boolean, steps: number): void;
    cut(): void;
    del(): void;
    deselect(): void;
    end(mark: boolean): void;
    findItem(text: string): number;
    getValidatorSettings(): DzSettings;
    hasAcceptableInput(): boolean;
    hasSelectedText(): boolean;
    home(mark: boolean): void;
    insertItem(index: number, item: string, validate: boolean): void;
    insertItems(index: number, items: any[], validate: boolean): void;
    items(): any[];
    paste(): void;
    redo(): void;
    removeItem(item: string): void;
    selectAll(): void;
    selectedText(): string;
    selectionStart(): number;
    setDoubleValidator(bottom: number, top: number, decimals: number, scientific: boolean): void;
    setIntValidator(bottom: number, top: number): void;
    setRegExValidator(rx: string, caseSensitive: boolean): void;
    setSelection(start: number, length: number): void;
    setValidator(settings: DzSettings): void;
    undo(): void;

    // SIGNALS
    cursorPositionChanged(oldPos: number, newPos: number): void;
    editingFinished(): void;
    itemChanged(item: string): void;
    returnPressed(): void;
    selectionChanged(): void;
    textChanged(text: string): void;
    textCleared(): void;
    textEdited(text: string): void;
}

/**
 * A “Compatibility Base” is described as an identifier that is used to represent the base concept of an object that can exist in the scene - e.g., a “Figure.” A “Compatibility Filter” is described as an identifier that is used to represent a specific shape of said object in the scene - e.g., a “Character.” Conceptually, compatibility bases support a hierarchical structure in a similar fashion, although not typically to the same depth, as categories. The “Compatibility Base” container type serves to provide a means of working with assets in order to define/determine which ones provide a particular object and/or which ones are regarded as being compatible with a particular object. See Also: DzAssetMgr :: getCompatibilityBases ()
 */
declare class DzCompatibilityBaseAssetContainer {
    isFilter(): boolean;
    isVendor: boolean;

    getPath(): string;
    updateChildren(): boolean;
}

/**
 * A specialization of DzModifier that provides an ability to conditionally “graft” (integrate) the geometry of a figure (i.e., a “follower” - a figure with the modifier), to the geometry of the figure it is following (i.e., a “follow target”). In horticultural terms, a “follower” serves the role of “scion” and a “follow target” serves the role of “stock.” This modifier also supports “culling” (hiding) facets in the geometry of a figure with the modifier, and separately in the geometry of the follow target, applied when the figure with the modifier is following another figure. Since: 4.9.2.1
 */
declare class DzConditionalGraftModifier {
    getTargetVertexCount(): number;
    getValueControl(): DzBoolProperty;
    setTargetVertexCount(vertCount: number): void;
}

/**
 * Represents a file in the content library that can be loaded/imported. Also provides functionality for moving the file to a new location, renaming the file, and deleting the file from the library. See Also: DzContentFolder
 */
declare class DzContentFile {
    canDelete(): boolean;
    canRename: boolean;
    companionIsScript: boolean;
    companionPath: string;
    fullPath: string;
    hasCompanion: boolean;
    hasCompanionScript: boolean;
    isNative: boolean;
    isScript: boolean;
    label: string;
    name: string;
    thumbnailPixmap: Pixmap;
    thumbnailSmallPixmap: Pixmap;
    icon: Pixmap;
    smallIcon: Pixmap;

    deleteFile(): boolean;
    getFolder(): DzContentFolder;
    getNext(): DzContentFile;
    reloadIcon(): void;
    rename(newName: string): boolean;
}

/**
 * Represents a folder in the content library that holds DzContentFile objects as well as other DzContentFolder objects. See Also: DzContentMgr :: getContentDirectory () DzContentMgr :: getImportDirectory () DzContentMgr :: getPoserDirectory () DzContentMgr :: findBaseDirectory ()
 */
declare class DzContentFolder {
    canAddSubFolder(): boolean;
    canDelete: boolean;
    canRename: boolean;
    filesAreLoaded: boolean;
    folderName: string;
    foldersAreLoaded: boolean;
    folderType: FolderType;
    fullPath: string;
    isBuiltInContentFolder: boolean;
    label: string;
    thumbnailPixmap: Pixmap;
    icon: Pixmap;

    addSubFolder(folderName: string): boolean;
    canMoveFile(file: DzContentFile): boolean;
    copyFile(file: DzContentFile): boolean;
    deleteFolder(): boolean;
    getFirstFile(): DzContentFile;
    getFirstFolder(): DzContentFolder;
    getFirstHiddenFile(): DzContentFile;
    getFirstHiddenFolder(): DzContentFolder;
    getNext(): DzContentFolder;
    getParent(): DzContentFolder;
    hasSubFolders(): boolean;
    isModifiable(): boolean;
    loadFiles(): void;
    loadFolders(): void;
    moveFile(file: DzContentFile): boolean;
    refresh(reloadThumbnails: boolean): boolean;
    rename(newName: string): boolean;
    unloadFiles(): void;
    unloadFolders(): void;

    // SIGNALS
    addedFolder(newFolder: DzContentFolder): void;
    fileListChanged(): void;
    folderListChanged(): void;
    removedFolder(folder: DzContentFolder): void;
}

/**
 * Responsible for the management of folder/file hierarchies associated with “content” (digital assets). There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getContentMgr (). See Also: Global :: App DzAssetMgr
 */
declare class DzContentMgr {
    autoRefresh(): boolean;
    maxRecentFiles: number;
    newScene: string;
    showBuiltInContent: boolean;
    startupScene: string;

    getCloudPathPrefix(): string;
    getContentPath(node: DzNode): string;
    addContentDirectory(directory: string, saveSetting: boolean): void;
    addImportDirectory(directory: string, saveSetting: boolean): void;
    addMDLDirectory(directory: string, saveSetting: boolean): void;
    addPoserDirectory(directory: string, saveSetting: boolean): void;
    addRecentFile(filename: string): void;
    clearRecentFileList(): void;
    contentDirectoryIsMapped(dirPath: string): boolean;
    doContentSearch(): boolean;
    doDirNumCheck(): void;
    fileCreated(filename: string): void;
    findBaseDirectory(dirTypes: DirectoryTypes, path: string): DzContentFolder;
    findBaseDirectory(path: string, useImportFolders: boolean): DzContentFolder;
    findFile(partialPath: string, dirTypes: DirectoryTypes): string;
    findSourcePathForNode(sceneNode: DzNode): string;
    getAbsolutePath(dirTypes: DirectoryTypes, relativePath: string, preferredPath: string): string;
    getAbsolutePath(relativePath: string, useImportFolders: boolean, preferredPath: string): string;
    getAbsolutePaths(dirTypes: DirectoryTypes, relativePath: string): any[];
    getAbsolutePaths(relativePath: string, useImportFolders: boolean): any[];
    getAbsoluteUri(dirTypes: DirectoryTypes, relativePath: string, preferredPath: string): DzUri;
    getBuiltInContentDirectory(): DzContentFolder;
    getBuiltInContentDirectoryPath(): string;
    getBuiltInMDLDirectory(which: number): DzContentFolder;
    getBuiltInMDLDirectoryPath(which: number): string;
    getCloudAbsolutePath(relativePath: string): string;
    getCloudContentDirectory(): DzContentFolder;
    getCloudContentDirectoryPath(): string;
    getCloudRelativePath(absolutePath: string): string;
    getContentDirectory(which: number): DzContentFolder;
    getContentDirectoryPath(which: number): string;
    getContentReplaceMgr(): DzContentReplaceMgr;
    getDefaultContentDirectoryPath(): string;
    getDefaultSharedContentDirectoryPath(): string;
    getDirectoryContentsUrisList(dirTypes: DirectoryTypes, relativeDirPaths: any[], fileSuffixes: any[]): any[];
    getImportAbsolutePath(relativePath: string): string;
    getImportDirectory(which: number): DzContentFolder;
    getImportDirectoryPath(which: number): string;
    getImportFileExtensions(): any[];
    getMappedPath(path: string, useImportFolders: boolean, isRelative: boolean): string;
    getMappedPath(dirTypes: DirectoryTypes, path: string, isRelative: boolean): string;
    getMDLAbsolutePath(relativePath: string): string;
    getMDLDirectory(which: number): DzContentFolder;
    getMDLDirectoryPath(which: number): string;
    getMDLRelativePath(absolutePath: string): string;
    getNativeAbsolutePath(relativePath: string): string;
    getNativeBaseUserFacingExcludedDirs(): any[];
    getNativeFileExtensions(): any[];
    getNumBuiltInMDLDirectories(): number;
    getNumContentDirectories(): number;
    getNumImportDirectories(): number;
    getNumMDLDirectories(): number;
    getNumPoserDirectories(): number;
    getPoserAbsolutePath(relativePath: string): string;
    getPoserBaseUserFacingDirs(): any[];
    getPoserDirectory(which: number): DzContentFolder;
    getPoserDirectoryPath(which: number): string;
    getPoserFileExtensions(): any[];
    getRecentFileList(): any[];
    getRelativePath(absolutePath: string, useImportFolders: boolean): string;
    getRelativePath(dirTypes: DirectoryTypes, absolutePath: string): string;
    getRelativePaths(dirTypes: DirectoryTypes, absolutePath: string): any[];
    getRelativePaths(absolutePath: string, useImportFolders: boolean): any[];
    getRelativeUrisList(dirTypes: DirectoryTypes, relDirPaths: any[], filters: Filters, suffixes: any[], recurse: boolean): any[];
    importDirectoryIsMapped(dirPath: string): boolean;
    importFile(path: string): boolean;
    isDirectoryMapped(directory: string): boolean;
    isUserFacingDirectoryPath(dirTypes: DirectoryTypes, relativePath: string): boolean;
    isUserFacingFilePath(dirTypes: DirectoryTypes, relativePath: string): boolean;
    loadAsset(asset: DzAsset, merge: boolean): boolean;
    loadAsset(asset: DzAsset): boolean;
    mdlDirectoryIsMapped(dirPath: string): boolean;
    mergeFiles(filenames: any[]): boolean;
    openFile(filename: string, merge: boolean): boolean;
    openNativeFile(filename: string, merge: boolean): boolean;
    openNativeUri(uri: DzUri, filename: string, merge: boolean): boolean;
    openUri(uri: DzUri, filename: string, merge: boolean): boolean;
    poserDirectoryIsMapped(dirPath: string): boolean;
    refresh(reloadIcons: boolean): void;
    reloadAssetsFromSource(sceneNode: DzNode, settings: DzSettings, srcFilePath: string): DzError;
    reloadSceneAssetsFromSource(settings: DzSettings): boolean;
    removeAllContentDirectories(): void;
    removeAllImportDirectories(): void;
    removeAllMDLDirectories(): void;
    removeAllPoserDirectories(): void;
    removeContentDirectory(directory: string): boolean;
    removeImportDirectory(directory: string): boolean;
    removeMDLDirectory(directory: string): boolean;
    removePoserDirectory(directory: string): boolean;
    saveAllMappedDirectories(): void;
    setCheckCompatibilityOn(useCheckCompatibility: boolean): void;
    setCloudContentDirectory(directory: string, saveSetting: boolean): void;
    setContentDirectories(directories: any[], saveSettings: boolean): void;
    setImportDirectories(directories: any[], saveSettings: boolean): void;
    setPoserDirectories(directories: any[], saveSettings: boolean): void;
    setUseDatabaseSearch(useDatabase: boolean): void;
    shouldMerge(filename: string): boolean;
    usingCheckCompatibility(): boolean;
    usingDatabaseSearch(): boolean;

    // SIGNALS
    autoRefreshChanged(onOff: boolean): void;
    cloudContentDirectoryChanged(): void;
    contentDirectoryListChanged(): void;
    folderTreeChanged(): void;
    importDirectoryListChanged(): void;
    loadScriptFinished(): void;
    loadScriptStarting(): void;
    mdlDirectoryListChanged(): void;
    newFileCreated(filename: string): void;
    onNewSceneChanged(filename: string): void;
    poserDirectoryListChanged(): void;
    recentFileListChanged(): void;
    scriptFailed(filename: string): void;
    scriptFinished(filename: string): void;
    scriptLoadFailed(filename: string): void;
    scriptLoadStarting(filename: string): void;
    scriptStarting(filename: string): void;
    startupSceneChanged(filename: string): void;
}

/**
 * Responsible for the management of replacing scene items based on their respective content types. There is only one instance of this manager in an application. This instance is created and owned by DzContentMgr . Request the instance via DzContentMgr :: getContentReplaceMgr (). See Also: Global :: App DzApp :: getContentMgr () DzAssetMgr DzAssetMgr :: getTypeForNode () DzAssetMgr :: getTypeForContentFile () DzAssetMgr :: isClothingType () DzAssetMgr :: isFigureType () DzAssetMgr :: isFollowingType () DzAssetMgr :: isHairType () DzAssetMgr :: isNeedsBaseFigureType () DzAssetMgr :: isPresetForFigureType () DzAssetMgr :: isPresetType () DzAssetMgr :: isPropType () DzAssetMgr :: isReplaceableType ()
 */
declare class DzContentReplaceMgr {
    clearReplaceData(): void;
    doReplace(): void;
    getDefaultReplaceNodeList(baseNode: DzNode): any[];
    getNewContentPath(): string;
    getNewContentType(): string;
    getPotentialReplaceNodeList(baseNode: DzNode): any[];
    getReplaceMode(): ContentReplaceMode;
    getReplaceNodeList(): any[];
    initReplaceForContentLoad(path: string, baseNode: DzNode): void;
    removeReplaceNodes(): void;
    setNewContentPath(contentPath: string): void;
    setNewContentType(contentType: string): void;
    setReplaceMode(mode: ContentReplaceMode): void;
    setReplaceNodes(replaceNodes: any[]): void;
    updateReplaceNodes(baseNode: DzNode): void;

    // SIGNALS
    contentReplaceModeChanged(mode: ContentReplaceMode): void;
}

/**
 * The controller class is like a modifier for DzProperty types. Controllers allow implementation of custom modulation of properties without changing the properties actual value. Common implementations of controllers include: controllers that adjust one property based on the value of another property, controllers that replace the value of one property with the value of another property, controllers that use a script expression to drive a property, etc.
 */
declare class DzController {
    description(): string;
    effect: ControllerEffect;
    slaveDescription: string;

    getOwner(): DzProperty;

    // SIGNALS
    attributeChanged(): void;
    currentValueChanged(): void;
}

/**
 * See Also: DzExportMgr :: findExporterByClassName () DzExportMgr :: findExporter () Sample: Export TriAx to Poser
 */
declare class DzCr2Exporter {
}

/**
 * TODO: Add detailed description.
 */
declare class DzCreateItemAction {
}

/**
 * This class represents a script based action that the user can create themselves. See Also: DzActionMgr :: getCustomAction () DzActionMgr :: addCustomAction () DzActionMgr :: setCustomActionText () DzActionMgr :: setCustomActionDescription () DzActionMgr :: setCustomActionScript () DzActionMgr :: setCustomActionShortcut () DzActionMgr :: setCustomActionIcon () DzActionMgr :: setCustomActionShowTextWithIcon () DzActionMgr :: removeCustomAction () DzActionMgr :: removeAllCustomActions (); DzActionMgr :: getNumCustomActions () DzActionMgr :: findCustomAction () DzActionMgr :: getCustomActionByIndex () DzActionMgr :: getCustomActionName () DzActionMgr :: getCustomActionText () DzActionMgr :: getCustomActionDescription () DzActionMgr :: getCustomActionScript () DzActionMgr :: getCustomActionFile () DzActionMgr :: getCustomActionShortcut () DzActionMgr :: getCustomActionIcon () DzActionMgr :: findActionsForShortcut () Since: 4.12.1.63
 */
declare class DzCustomAction {
}

/**
 * Represents a custom data item that can be: defined by a plug-in associated with the scene or elements of the scene saved to file with the scene object that owns it loaded from file when the owning object is loaded
 */
declare class DzCustomData {
    isPersistent(): boolean;
}

/**
 * This is the script counterpart to the QDateTime type used in the C++ SDK. Date Time String Format ECMAScript defines a string interchange format for date-times based upon a simplification of the ISO 8601 Extended Format. The format is as follows: YYYY-MM-DDTHH:mm:ss.sssZ Where the fields are as follows: YYYY - is the decimal digits of the year 0000 to 9999 in the Gregorian calendar. - - (hyphen) appears literally twice in the string; once between the year/month fields, and once between the month/day fields. MM - is the month of the year from 01 (January) to 12 (December). DD - is the day of the month from 01 to 31. T - appears literally in the string, to indicate the beginning of the time element. HH - is the number of complete hours that have passed since midnight as two decimal digits from 00 to 24. : - (colon) appears literally twice in the string; once between the hour/minute fields, and once between the minute/seconds fields. mm - is the number of complete minutes since the start of the hour as two decimal digits from 00 to 59. ss - is the number of complete seconds since the start of the minute as two decimal digits from 00 to 59. . - (dot) appears literally in the string; between the seconds and milliseconds fields. sss - is the number of complete milliseconds since the start of the second as three decimal digits. Z - is the time zone offset specified as “Z” (for UTC) or either “+” or “-” followed by a time expression HH:mm This format includes the date-only forms: YYYY YYYY-MM YYYY-MM-DD It also includes date-time forms that consist of one of the above date-only forms immediately followed by one of the following time forms with an optional time zone offset appended: THH:mm THH:mm:ss THH:mm:ss.sss
 */
declare class Date {
    now(): number;
    parse(dateString: string): number;
    UTC(year: number, month: number, date: number, hour: number, minutes: number, seconds: number, milliseconds: number): number;
    getDate(): number;
    getDay(): number;
    getFullYear(): number;
    getHours(): number;
    getMilliseconds(): number;
    getMinutes(): number;
    getMonth(): number;
    getSeconds(): number;
    getTime(): number;
    getTimezoneOffset(): number;
    getUTCDate(): number;
    getUTCDay(): number;
    getUTCFullYear(): number;
    getUTCHours(): number;
    getUTCMilliseconds(): number;
    getUTCMinutes(): number;
    getUTCMonth(): number;
    getUTCSeconds(): number;
    getYear(): number;
    setDate(dayOfTheMonth: number): void;
    setFullYear(year: number, ...args: any[]): void;
    setHours(hours: number, ...args: any[]): void;
    setMilliseconds(milliseconds: number): void;
    setMinutes(minutes: number, ...args: any[]): void;
    setMonth(month: number, ...args: any[]): void;
    setSeconds(seconds: number, ...args: any[]): void;
    setTime(milliseconds: number): void;
    setUTCDate(dayOfTheMonth: number): void;
    setUTCFullYear(year: number, ...args: any[]): void;
    setUTCHours(hours: number, ...args: any[]): void;
    setUTCMilliseconds(milliseconds: number): void;
    setUTCMinutes(minutes: number, ...args: any[]): void;
    setUTCMonth(month: number, ...args: any[]): void;
    setUTCSeconds(seconds: number, ...args: any[]): void;
    setYear(year: number, ...args: any[]): void;
    toDateString(): string;
    toISOString(): string;
    toJSON(): string;
    toLocaleDateString(): string;
    toLocaleString(): string;
    toLocaleTimeString(): string;
    toString(): string;
    toTimeString(): string;
    toUTCString(): string;
    valueOf(): number;
    toGMTString(): string;
}

/**
 * Provides a date editor.
 */
declare class DzDateEdit {
    max(): Date;
    min: Date;
    separator: string;

    // SIGNALS
    valueChanged(date: Date): void;
}

/**
 * Provides a combination date and time editor.
 */
declare class DzDateTimeEdit {
    date(): Date;
    dateMax: Date;
    dateMin: Date;
    dateTime: Date;
    displayFormat: string;
    time: Date;
    timeMax: Date;
    timeMin: Date;
    dateSeparator: string;
    timeSeparator: string;

    // SIGNALS
    valueChanged(dateTime: Date): void;
}

/**
 * Provides the ability to post three dimensional debugging information, such as points and/or lines, to the scene and thereby cause it to be drawn within a view of the scene - e.g., in a viewport. Each instance of this object maintains a list of points and/or lines. Each set of points and/or lines is defined in terms of a “channel.” Each channel is identified by a number - point channels and line channels are defined independent of one another, but may use the same identifier to establish a weak association between them. Each channel is assigned a color at creation. Basic workflow is to create a point/line channel, add points/lines to the channel, then post the debug data. Example: Attention: Instances of this object are intended for developers that want to visualize three dimensional debugging information, not for display to end users. No attempt is made to prevent one instance of this object from trampling over the debugging information posted to the scene by another instance. Since: 4.11.0.216
 */
declare class DzDebugViewUtil {
    addLine(channel: number, startPosWS: DzVec3, endPosWS: DzVec3): void;
    addPoint(channel: number, posWS: DzVec3): void;
    clearChannels(): void;
    clearChannelsFromScene(): void;
    createLineChannel(channel: number, color: { r: number, g: number, b: number, a: number }, range: DzTimeRange): void;
    createPointChannel(channel: number, color: { r: number, g: number, b: number, a: number }, range: DzTimeRange): void;
    postDebugData(): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzDefaultMaterial {
    getAmbientColor(): { r: number, g: number, b: number, a: number };
    getAmbientColorControl(): DzColorProperty;
    getAmbientColorMap(): DzTexture;
    getAmbientStrength(): number;
    getAmbientStrengthControl(): DzFloatProperty;
    getAmbientValueMap(): DzTexture;
    getBumpControl(): DzFloatProperty;
    getBumpMap(): DzTexture;
    getBumpMax(): number;
    getBumpMaxControl(): DzFloatProperty;
    getBumpMin(): number;
    getBumpMinControl(): DzFloatProperty;
    getBumpStrength(): number;
    getDiffuseColorControl(): DzColorProperty;
    getDiffuseStrength(): number;
    getDiffuseStrengthControl(): DzFloatProperty;
    getDiffuseValueMap(): DzTexture;
    getDisplacementControl(): DzFloatProperty;
    getDisplacementMap(): DzTexture;
    getDisplacementMax(): number;
    getDisplacementMaxControl(): DzFloatProperty;
    getDisplacementMin(): number;
    getDisplacementMinControl(): DzFloatProperty;
    getDisplacementStrength(): number;
    getGlossinessControl(): DzFloatProperty;
    getGlossinessStrength(): number;
    getGlossinessValueMap(): DzTexture;
    getHorizontalOffset(): number;
    getHorizontalOffsetControl(): DzFloatProperty;
    getHorizontalTiles(): number;
    getHorizontalTilesControl(): DzFloatProperty;
    getIndexOfRefraction(): number;
    getIndexOfRefractionControl(): DzFloatProperty;
    getMultThroughOpacityControl(): DzBoolProperty;
    getNormalValueMap(): DzTexture;
    getNormalValueMapControl(): DzImageProperty;
    getOpacityControl(): DzFloatProperty;
    getReflectionColor(): { r: number, g: number, b: number, a: number };
    getReflectionColorControl(): DzColorProperty;
    getReflectionMap(): DzTexture;
    getReflectionStrength(): number;
    getReflectionStrengthControl(): DzFloatProperty;
    getReflectionValueMap(): DzTexture;
    getRefractionColor(): { r: number, g: number, b: number, a: number };
    getRefractionColorControl(): DzColorProperty;
    getRefractionColorMap(): DzTexture;
    getRefractionStrength(): number;
    getRefractionStrengthControl(): DzFloatProperty;
    getRefractionValueMap(): DzTexture;
    getScatterColor(): { r: number, g: number, b: number, a: number };
    getScatterColorControl(): DzColorProperty;
    getScatterColorMap(): DzTexture;
    getSheenColor(): { r: number, g: number, b: number, a: number };
    getSheenColorControl(): DzColorProperty;
    getSheenColorMap(): DzTexture;
    getSpecularColor(): { r: number, g: number, b: number, a: number };
    getSpecularColorControl(): DzColorProperty;
    getSpecularColorMap(): DzTexture;
    getSpecularStrength(): number;
    getSpecularStrengthControl(): DzFloatProperty;
    getSpecularValueMap(): DzTexture;
    getSurfaceType(): number;
    getSurfaceTypeControl(): DzEnumProperty;
    getThickness(): number;
    getThicknessControl(): DzFloatProperty;
    getThicknessValueMap(): DzTexture;
    getVerticalOffset(): number;
    getVerticalOffsetControl(): DzFloatProperty;
    getVerticalTiles(): number;
    getVerticalTilesControl(): DzFloatProperty;
    isMultThroughOpacity(): boolean;
    needsTangentSpaceParams(): boolean;
    setAmbientColor(color: { r: number, g: number, b: number, a: number }): void;
    setAmbientColorMap(img: DzTexture): void;
    setAmbientStrength(val: number): void;
    setAmbientValueMap(img: DzTexture): void;
    setBumpMap(img: DzTexture): void;
    setBumpMax(val: number): void;
    setBumpMin(val: number): void;
    setBumpStrength(val: number): void;
    setDiffuseStrength(val: number): void;
    setDiffuseValueMap(img: DzTexture): void;
    setDisplacementMap(img: DzTexture): void;
    setDisplacementMax(val: number): void;
    setDisplacementMin(val: number): void;
    setDisplacementStrength(val: number): void;
    setGlossinessStrength(size: number): void;
    setGlossinessValueMap(img: DzTexture): void;
    setHorizontalOffset(offset: number): void;
    setHorizontalTiles(tiles: number): void;
    setIndexOfRefraction(val: number): void;
    setMultThroughOpacity(onOff: boolean): void;
    setNormalValueMap(img: DzTexture): void;
    setReflectionColor(color: { r: number, g: number, b: number, a: number }): void;
    setReflectionMap(img: DzTexture): void;
    setReflectionStrength(val: number): void;
    setReflectionValueMap(img: DzTexture): void;
    setRefractionColor(color: { r: number, g: number, b: number, a: number }): void;
    setRefractionColorMap(img: DzTexture): void;
    setRefractionStrength(val: number): void;
    setRefractionValueMap(img: DzTexture): void;
    setScatterColor(color: { r: number, g: number, b: number, a: number }): void;
    setScatterColorMap(arg0: DzTexture): void;
    setSheenColor(color: { r: number, g: number, b: number, a: number }): void;
    setSheenColorMap(arg0: DzTexture): void;
    setSpecularColor(color: { r: number, g: number, b: number, a: number }): void;
    setSpecularColorMap(img: DzTexture): void;
    setSpecularStrength(size: number): void;
    setSpecularValueMap(img: DzTexture): void;
    setSurfaceType(val: number): void;
    setThickness(arg0: number): void;
    setThicknessValueMap(arg0: DzTexture): void;
    setVerticalOffset(offset: number): void;
    setVerticalTiles(tiles: number): void;
}

/**
 * Implements a RenderMan interface for the scene to render itself through the 3Delight renderer.
 */
declare class DzDelightRenderer {
    resetIPRHandler(): void;
}

/**
 * Provides information about the user's desktop, such as its total size, number of screens, the geometry of each screen, and whether they are configured as separate desktops or a single virtual desktop. Since: 4.7.1.x
 */
declare class DzDesktopWidget {
    primaryScreen(): number;
    screenCount: number;
    virtualDesktop: boolean;

    availableGeometry(screen: number): Rect;
    availableGeometry(widget: QWidget): Rect;
    availableGeometry(point: Point): Rect;
    screen(index: number): any;
    screenGeometry(point: Point): Rect;
    screenGeometry(screen: number): Rect;
    screenGeometry(widget: QWidget): Rect;
    screenNumber(point: Point): number;
    screenNumber(widget: QWidget): number;

    // SIGNALS
    resized(screen: number): void;
    screenCountChanged(newCount: number): void;
    workAreaResized(screen: number): void;
}

/**
 * Deprecated Exists only to keep old code working. Do not use in new code. Use DzDesktopWidget instead. This page exists in order to indicate the script accessible properties and signals of the Qt native QDesktopWidget class. Use Global :: getDesktop () to retrieve an object of this type.
 */
declare class QDesktopWidget {
    primaryScreen(): number;
    screenCount: number;
    virtualDesktop: boolean;

    // SIGNALS
    resized(screen: number): void;
    screenCountChanged(newCount: number): void;
    workAreaResized(screen: number): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzDevice {
    getDefaultSettings(settings: DzSettings): void;
    getDescription(): string;
    getDeviceName(): string;
    getSettings(settings: DzSettings): void;
    setSettings(settings: DzSettings): void;
}

/**
 * Responsible for the management of hardware devices. There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getDeviceMgr (). See Also: Global :: App DzDevice
 */
declare class DzDeviceMgr {
    getDevice(which: number): DzDevice;
    getNumDevices(): number;
}

/**
 * The dForm is the primary component of a dForm deformer. The others are the DzDFormBase , DzDFormZone and DzDFormModifier .
 */
declare class DzDForm {
    applyToNode(node: DzNode): void;
    getAvatarScale(): number;
    getAvatarScaleControl(): DzFloatProperty;
    getBase(): DzDFormBase;
    getGradientMax(): { r: number, g: number, b: number, a: number };
    getGradientMin(): { r: number, g: number, b: number, a: number };
    getInfluenceMode(): InfluenceMode;
    getModifier(i: number): DzDFormModifier;
    getModifierForNode(node: DzNode): DzDFormModifier;
    getNumModifiers(): number;
    getOpacity(): number;
    getOpacityControl(): DzFloatProperty;
    getZone(): DzDFormZone;
    setAvatarScale(val: number): void;
    setBase(base: DzDFormBase): void;
    setGradientMax(color: { r: number, g: number, b: number, a: number }): void;
    setGradientMin(color: { r: number, g: number, b: number, a: number }): void;
    setOpacity(val: number): void;
    setZone(zone: DzDFormZone): void;

    // SIGNALS
    dformModifierListChanged(): void;
}

/**
 * An asset save filter for saving a D-Former(s) Preset in the DSON format. See Also: Sample: Save a D-Former(s) Preset
 */
declare class DzDFormAssetFilter {
}

/**
 * The base is one component of a dForm deformer. The others are the DzDForm , DzDFormZone and DzDFormModifier . The dForm base functions as the origin for the dForm deformation effect, as detailed in the dForm class. The dForm base and zone can be created separately from the dForm and then joined together with the addDForm(), addZone(), etc functions.
 */
declare class DzDFormBase {
    getDForm(): DzDForm;
}

/**
 * The dForm modifier is the modifier component of a dForm deformer. The others are the DzDFormBase , DzDFormZone and DzDForm . A DzDFormModifier generates a local space delta for the vertices in the target geometry based on the dForm component parameters. It also draws the vertex weight points. It can be used to spawn a morph from the dForm on the target geometry. The dForm modifier is coded for one-to-one dForm and target relationships. Setting a new dForm/target pair replaces the old pair. Generally a DzDFormModifier should not be created by the user but rather generated by a DzDForm node itself using DzDForm :: applyToNode ().
 */
declare class DzDFormModifier {
    assetAuthor(): DzAuthor;
    assetFileRevision: DzVersion;
    assetId: string;
    assetModifiedDate: Date;
    assetNeedSave: boolean;
    assetSource: DzUri;
    assetUri: DzUri;

    clearAltDFormer(): void;
    createAltGeomDFormer(atFront: boolean): DzDFormModifier;
    getDForm(): DzDForm;
    getInfluenceWeights(): DzWeightMap;
    getMaskBone(): DzBone;
    getValueControl(): DzFloatProperty;
    invalidateInfluenceWeights(): void;
    isAppliedAsLegacy(): boolean;
    modifyAsset(): boolean;
    modifyAsset(newUri: DzUri): boolean;
    setApplyAsLegacy(onOff: boolean): void;
    setDForm(dform: DzDForm): void;
    setInfluenceWeights(map: DzWeightMap): DzError;
    setMaskBone(bone: DzBone): void;
    setWeightMapFromZone(map: DzWeightMap, node: DzNode): DzError;
    spawnMorph(node: DzNode, name: string): DzMorph;

    // SIGNALS
    assetModified(): void;
    assetWasSaved(): void;
    dformChanged(newDForm: DzDForm): void;
    weightListChanged(): void;
    weightsChanged(): void;
}

/**
 * The zone is one component of a dForm deformer. The others are the DzDForm , DzDFormBase and DzDFormModifier . The zone is an independent DzNode derived object that is used to set the area of influence of the dForm's effect. It is spherical in shape but can be scaled into any form of ellipsoid. The zone has an effect falloff zone based on a naturalspline_dz object. The falloff is the same along the x,y and z axis. The zone has draws itself as a wireframe sphere. The base size of this sphere is controlled by the DzFloatProperty “Radius”. This sphere can be made transparent and is controlled by the DzFloatProperty “Opacity”. The zone is drawn with the maximum gradient color of the dForm.
 */
declare class DzDFormZone {
    getDForm(): DzDForm;
    getInfluenceMode(): InfluenceMode;
    getInfluenceModeControl(): DzEnumProperty;
    getOpacityControl(): DzFloatProperty;
    getSpline(): naturalspline_dz;

    // SIGNALS
    influenceModeChanged(): void;
}

/**
 * Provides a rounded range control like a speedometer.
 */
declare class DzDial {
    lineStep(): number;
    max: number;
    min: number;
    notchesVisible: boolean;
    notchSize: number;
    notchTarget: number;
    pageStep: number;
    tracking: boolean;
    value: number;
    wrapping: boolean;

    // SIGNALS
    dialMoved(value: number): void;
    dialPressed(): void;
    dialReleased(): void;
    valueChanged(value: number): void;
}

/**
 * This is the basic building block for script interfaces. DzDialog provides an independent window widget that can act as the parent for other script widgets. Most custom script interfaces will be built starting with a DzDialog (or subclass) customized with DzLayout and DzWidget components.
 */
declare class DzDialog {
    caption(): string;
    orientation: Orientation;
    sizeGripEnabled: boolean;

    close(): boolean;
    exec(): boolean;
    extension(): DzWidget;
    hideExtension(): void;
    setAcceptButton(btn: DzButton): void;
    setExtension(extension: DzWidget): void;
    setRejectButton(btn: DzButton): void;
    showExtension(onOff: boolean): void;
    showExtension(): void;
}

/**
 * Provides access to the file system directory structure. It provides functions for creating, removing, traversing, and searching directories.
 */
declare class DzDir {
    cleanPath(path: string): string;
    current(): DzDir;
    currentPath(): string;
    fromNativeSeparators(pathName: string): string;
    home(): DzDir;
    homePath(): string;
    isAbsolutePath(path: string): boolean;
    isRelativePath(path: string): boolean;
    match(filter: string, fileName: string): boolean;
    match(filters: any[], fileName: string): boolean;
    root(): DzDir;
    rootPath(): string;
    separator(): string;
    setCurrent(path: string): boolean;
    temp(): DzDir;
    tempPath(): string;
    toNativeSeparators(pathName: string): string;
    absoluteFilePath(fileName: string): string;
    absolutePath(): string;
    canonicalPath(): string;
    cd(dirName: string): boolean;
    cdUp(): boolean;
    copy(srcFile: string, destFile: string): boolean;
    count(): number;
    dirName(): string;
    entryList(nameFilter: string, filters: Filters, sort: SortFlags): any[];
    entryList(nameFilters: any[], filters: Filters, sort: SortFlags): any[];
    entryList(filters: Filters, sort: SortFlags): any[];
    exists(): boolean;
    exists(name: string): boolean;
    filePath(fileName: string): string;
    filter(): Filters;
    getFilesFromDir(extentions: any[], recursive: boolean): any[];
    isAbsolute(): boolean;
    isReadable(): boolean;
    isRelative(): boolean;
    isRoot(): boolean;
    makeAbsolute(): boolean;
    mkdir(dirName: string): boolean;
    mkpath(dirpath: string): boolean;
    move(srcFile: string, destFile: string): boolean;
    nameFilters(): any[];
    path(): string;
    refresh(): void;
    relativeFilePath(fileName: string): string;
    remove(fileName: string): boolean;
    rename(oldName: string, newName: string): boolean;
    rmdir(dirName: string): boolean;
    rmpath(dirPath: string): boolean;
    setCurrent(): boolean;
    setFilter(filters: Filters): void;
    setNameFilters(nameFilters: any[]): void;
    setPath(path: string): void;
    setSorting(sort: SortFlags): void;
    sorting(): SortFlags;
    absFilePath(file: string): string;
    mkdirs(dirName: string): boolean;
    rmdirs(dirName: string): boolean;
    fileExists(fileName: string): boolean;
    absPath(): string;
}

/**
 * TODO: Add detailed description.
 */
declare class DzDistantLight {
    getDiffuseColor(): { r: number, g: number, b: number, a: number };
    getDiffuseColorControl(): DzColorProperty;
    getFarClippingPlane(): number;
    getFlux(): number;
    getIlluminationControl(): DzEnumProperty;
    getIntensity(): number;
    getIntensityControl(): DzFloatProperty;
    getIntensityScale(): number;
    getIntensityScaleControl(): DzFloatProperty;
    getLightFluxControl(): DzFloatProperty;
    getLightGeometry(): AreaShape;
    getLightGeometryControl(): DzEnumProperty;
    getLightHeight(): number;
    getLightHeightControl(): DzFloatProperty;
    getLightPortalControl(): DzBoolProperty;
    getLightTemperature(): number;
    getLightTemperatureControl(): DzFloatProperty;
    getLightTwoSided(): boolean;
    getLightTwoSidedControl(): DzBoolProperty;
    getLightWidth(): number;
    getLightWidthControl(): DzFloatProperty;
    getNearClippingPlane(): number;
    getPhotometricModeControl(): DzBoolProperty;
    getRenderEmitterControl(): DzBoolProperty;
    getShadowBiasControl(): DzFloatProperty;
    getShadowColorControl(): DzColorProperty;
    getShadowIntensityControl(): DzFloatProperty;
    getShadowSoftnessControl(): DzFloatProperty;
    getWSDirection(): DzVec3;
    isLightPortal(): boolean;
    isOn(): boolean;
    photometricMode(): boolean;
    renderEmitter(): boolean;
}

/**
 * TODO: Add detailed description.
 */
declare class DzDockArea {
    getColumn(which: number): DzDockAreaColumn;
    getNumColumns(): number;
}

/**
 * TODO: Add detailed description.
 */
declare class DzDockAreaColumn {
    depth(): number;
    getNumWindows(): number;
    getPreferredDepth(): number;
    getWindow(which: number): DzDockWindow;
    isMinimized(): boolean;
    minimize(): void;
    minimumDepth(): number;
    restore(): void;
    setPreferredDepth(depth: number): void;
    toggleMinimized(): void;
}

/**
 * This class provides access to a custom bar in the interface that can be docked with a DzToolBar . This class is not intended to be constructed directly, rather it serves as a base class for other custom dock-able bars. See Also: DzPaneMgr :: getNumDockBars () DzPaneMgr :: getDockBar () DzPaneMgr :: findDockBar () DzPaneMgr :: findDockBarByName () DzPaneMgr :: getDockBarList ()
 */
declare class DzDockBar {
    floating(): boolean;

    dock(area: DockArea, beforeBar: string): void;
    dockedArea(): DockArea;
    isClosed(): boolean;
    setClosed(onOff: boolean): void;
    undock(pos: Point): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzDockWindow {
    dock(): void;
    dock(area: DzDockArea, newColumn: boolean): void;
    dock(area: DzDockArea, columnNum: number): void;
    getArea(): DzDockArea;
    getColumnDimension(): number;
    getColumnNum(): number;
    getLastSize(): Size;
    getLength(): number;
    getMinimumLength(): number;
    getPreferredLength(): number;
    isDocked(): boolean;
    isLengthFixed(): boolean;
    isMinimized(): boolean;
    minimize(): void;
    restore(): void;
    setColumnDimension(dimension: number): void;
    setColumnNum(columnNum: number): void;
    setLength(length: number): void;
    setPreferredLength(length: number): void;
    setResizeHandlesVisible(yesNo: boolean): void;
    setTitleBarVisible(yesNo: boolean): void;
    toggleDock(): void;
    toggleMinimized(): void;
    undock(): void;

    // SIGNALS
    docked(): void;
    lengthChanged(): void;
    minimized(window: DzDockWindow): void;
    outlineDrawFinished(): void;
    outlineDrawStarting(): void;
    restored(window: DzDockWindow): void;
    undocked(): void;
}

/**
 * A script wrapper for QDomAttr . This object represents an “Attribute” of a “Element” ( DzDomElement ) in a DOM document. Instances of this object are not constructed directly, rather they are returned by calling DzDomDocument :: createAttribute (). An easier method of adding or setting an attribute on an element is to call DzDomElement :: setAttribute () on the element to which the attribute should be added or set.
 */
declare class DzDomAttr {
    name(): string;
    value: string;

    ownerElement(): DzDomNode;
    specified(): boolean;
}

/**
 * This object represents a basic, empty, node in a DOM document tree. Instances of this object are not constructed directly, rather they are potentially returned by various methods on instances of other Document Object Model (DOM) Objects if the node they represent is invalid (NULL).
 */
declare class DzDomBasicNode {
}

/**
 * A script wrapper for QDomCDATASection . This object represents a “CDATA Section” in a DOM document. CDATA Sections can contain special characters that would otherwise be interpreted as part of the markup language. This provides a way for embedding text that contains special characters without the need for escaping all those characters. Instances of this object are not constructed directly, rather they are returned by calling DzDomDocument :: createCDATASection ().
 */
declare class DzDomCDATASection {
}

/**
 * A script wrapper for QDomCharacterData . This object represents a generic data string in a DOM document. Specialized versions of this object are DzDomText , DzDomComment and DzDomCDATASection . Instances of this object are not constructed directly, rather instances of the specialized versions of this object are returned by calling DzDomDocument :: createTextNode (), DzDomDocument :: createComment () or DzDomDocument :: createCDATASection ().
 */
declare class DzDomCharacterData {
    data(): string;
    length: number;

    appendData(arg: string): void;
    deleteData(offset: number, count: number): void;
    insertData(offset: number, arg: string): void;
    replaceData(offset: number, count: number, arg: string): void;
    substringData(offset: number, count: number): string;
}

/**
 * A script wrapper for QDomComment . This object represents a “Comment” in a DOM document. Instances of this object are not constructed directly, rather they are returned by calling DzDomDocument :: createComment ().
 */
declare class DzDomComment {
}

/**
 * A script wrapper for QDomDocument . This object represents an entire DOM document. Conceptually, it is the root of the document tree and provides the primary access to the document's data. This is the only DzDomNode derived object that is constructed directly. To populate a document, use loadContent () to cause data to be parsed from an XML (or XML derivative) file, or use setContent () to cause data to be parsed from an XML (or XML derivative) string. Note that it is also possible to create nodes of the DOM tree from scratch by using the following factory functions: createElement () createDocumentFragment () createTextNode () createComment () createCDATASection () createProcessingInstruction () createAttribute () createEntityReference () createElementNS () createAttributeNS () The parsed XML data is represented by an internal tree of nodes that can be accessed using DzDomNode (and derived) objects. The internal objects in the DOM tree are deleted once the last DOM object referencing them and the DzDomDocument itself are deleted. For more information about the Document Object Model (DOM) see the Level 1 and Level 2 Core specifications.
 */
declare class DzDomDocument {
    createAttribute(name: string): DzDomAttr;
    createAttributeNS(nsURI: string, qName: string): DzDomAttr;
    createCDATASection(value: string): DzDomCDATASection;
    createComment(value: string): DzDomComment;
    createDocumentFragment(): DzDomDocumentFragment;
    createElement(tagName: string): DzDomElement;
    createElementNS(nsURI: string, qName: string): DzDomElement;
    createEntityReference(name: string): DzDomEntityReference;
    createProcessingInstruction(target: string, data: string): DzDomProcessingInstruction;
    createTextNode(value: string): DzDomText;
    doctype(): DzDomDocumentType;
    documentElement(): DzDomElement;
    elementById(id: string): DzDomNode;
    importNode(node: DzDomNode, deep: boolean): DzDomNode;
    loadContent(filename: string): boolean;
    saveContent(filename: string): boolean;
    setContent(text: string): boolean;
    toByteArray(indent: number): ByteArray;
    toString(indent: number): string;
}

/**
 * A script wrapper for QDomDocumentFragment . This object represents a tree of DzDomNode objects which are not usually a complete DzDomDocument . Instances of this object are not constructed directly, rather they are returned by calling DzDomDocument :: createDocumentFragment (). The most important feature of this object is the way it is treated by DzDomNode :: insertAfter (), DzDomNode :: insertBefore (), DzDomNode :: replaceChild () and DzDomNode :: appendChild (); instead of inserting the fragment itself, all of the fragment's children are inserted.
 */
declare class DzDomDocumentFragment {
}

/**
 * A script wrapper for QDomDocumentType . This object represents a “Document Type” node in a DOM document tree. Instances of this object are not constructed directly, rather they are retrieved from a DOM document by calling DzDomDocument :: doctype ().
 */
declare class DzDomDocumentType {
    internalSubset(): string;
    name: string;
    publicId: string;
    systemId: string;
}

/**
 * A script wrapper for QDomElement . This object represents an “Element” in a DOM document. Instances of this object are not constructed directly, rather they are returned by calling DzDomDocument :: createElement ().
 */
declare class DzDomElement {
    tagName(): string;

    attribute(name: string, defValue: string): string;
    attributeNode(name: string): DzDomNode;
    attributeNodeNS(nsURI: string, localName: string): DzDomNode;
    attributeNS(nsURI: string, localName: string, defValue: string): string;
    attributes(): any;
    elementsByTagName(tagName: string): any[];
    elementsByTagNameNS(nsURI: string, localName: string): any[];
    hasAttribute(name: string): boolean;
    hasAttributeNS(nsURI: string, localName: string): boolean;
    removeAttribute(name: string): void;
    removeAttributeNode(attr: DzDomAttr): DzDomNode;
    removeAttributeNS(nsURI: string, localName: string): void;
    setAttribute(name: string, value: string): void;
    setAttributeNode(attr: DzDomAttr): DzDomNode;
    setAttributeNodeNS(attr: DzDomAttr): DzDomNode;
    setAttributeNS(nsURI: string, qName: string, value: string): void;
}

/**
 * A script wrapper for QDomEntity . This object represents an “Entity” in a DOM document.
 */
declare class DzDomEntity {
    notationName(): string;
    publicId: string;
    systemId: string;
}

/**
 * A script wrapper for QDomEntityReference . This object represents an “Entity Reference” in a DOM document. Instances of this object are not constructed directly, rather they are returned by calling DzDomDocument :: createEntityReference ().
 */
declare class DzDomEntityReference {
}

/**
 * A script wrapper for QDomNode . This is an abstract base type that provides general functionality for Document Object Model (DOM) nodes. For more information about the Document Object Model (DOM) see the Level 1 and Level 2 Core specifications. For a more general introduction of the DOM implementation see the DzDomDocument documentation.
 */
declare class DzDomNode {
    localName(): string;
    namespaceURI: string;
    nodeName: string;
    nodeType: NodeType;
    nodeValue: string;
    prefix: string;

    appendChild(child: DzDomNode): void;
    childNodes(): any[];
    clear(): boolean;
    cloneNode(deep: boolean): DzDomNode;
    columnNumber(): number;
    firstChild(): DzDomNode;
    firstChildElement(tagName: string): DzDomNode;
    hasAttributes(): boolean;
    hasChildNodes(): boolean;
    insertAfter(newChild: DzDomNode, refChild: DzDomNode): void;
    insertBefore(newChild: DzDomNode, refChild: DzDomNode): void;
    isAttr(): boolean;
    isCDATASection(): boolean;
    isCharacterData(): boolean;
    isComment(): boolean;
    isDocument(): boolean;
    isDocumentFragment(): boolean;
    isDocumentType(): boolean;
    isElement(): boolean;
    isEntity(): boolean;
    isEntityReference(): boolean;
    isNotation(): boolean;
    isNull(): boolean;
    isProcessingInstruction(): boolean;
    isSupported(feature: string, version: string): boolean;
    isText(): boolean;
    lastChild(): DzDomNode;
    lastChildElement(tagName: string): DzDomNode;
    lineNumber(): number;
    namedItem(name: string): DzDomNode;
    nextSibling(): DzDomNode;
    nextSiblingElement(tagName: string): DzDomNode;
    normalize(): void;
    ownerDocument(): DzDomNode;
    parentNode(): DzDomNode;
    previousSibling(): DzDomNode;
    previousSiblingElement(tagName: string): DzDomNode;
    removeChild(oldChild: DzDomNode): void;
    replaceChild(newChild: DzDomNode, oldChild: DzDomNode): void;
}

/**
 * A script wrapper for QDomNotation . This object represents a “Notation” in a DOM document.
 */
declare class DzDomNotation {
    publicId(): string;
    systemId: string;
}

/**
 * A script wrapper for QDomProcessingInstruction . This object represents a “Processing Instruction” in a DOM document. Instances of this object are not constructed directly, rather they are returned by calling DzDomDocument :: createProcessingInstruction ().
 */
declare class DzDomProcessingInstruction {
    data(): string;
    target: string;
}

/**
 * A script wrapper for QDomText . This object represents “Text” data in a DOM document. Instances of this object are not constructed directly, rather they are returned by calling DzDomDocument :: createTextNode ().
 */
declare class DzDomText {
    splitText(offset: number): DzDomNode;
}

/**
 * TODO: Add detailed description.
 */
declare class DzDrawStyle {
    drawCuesDefault(): boolean;
    drawObjectsOnly: boolean;
    drawShadowCastersOnly: boolean;
    isUserStyle: boolean;
    renderQuality: boolean;

    drawCues(): boolean;
    forceUseLighting(): void;
    pass(): number;
    regionsEnabled(): boolean;
    selectionMapsEnabled(): boolean;
    shader(): sceneshader_dz;
    shadeStyle(): ShadeStyle;
}

/**
 * A Dynamic Divider takes two DzWidget objects and places a divider bar between them. It handles resize events, as well as toggling of the divider bar if toggling is enabled. For complex arrangements you can nest instances of this class by specifying them as one of the widgets via setFirstWidget ( DzWidget ) or setSecondWidget ( DzWidget ) See Also: DzSplitter
 */
declare class DzDynamicDividerWgt {
    actualDividerPercent(): number;
    dividerOrientation: DividerOrientation;
    dividerType: BarStyle;
    margin: number;
    minimized: boolean;
    moveDisabled: boolean;
    preferredDividerPercent: number;
    preferredWidget: WidgetType;
    preferredWidgetExtent: number;
    spacing: number;
    toggleDirection: WidgetType;
    toggleEnabled: boolean;

    moveDivider(distance: number): void;
    setDividerBar(orientation: DividerOrientation, barStyle: BarStyle): void;
    setFirstWidget(first: DzWidget): void;
    setPreferredWidgetExtent(widget: WidgetType, extent: number): void;
    setSecondWidget(second: DzWidget): void;
    setToggleState(minimized: boolean): void;
    swapFirstAndSecondWidgets(): void;
    toggleWidget(): void;
}

/**
 * Represents an edge between two vertices.
 */
declare class DzEdge {
    cageOffsetA(): number;
    facetA: number;
    facetB: number;
    index: number;
    offsetA: number;
    offsetB: number;
    vertIdx1: number;
    vertIdx2: number;

    isOpenEdge(): boolean;
    toString(): string;
}

/**
 * TODO: Add detailed description.
 */
declare class DzEditAction {
}

/**
 * Classes derived from DzElement may have any number of properties (objects derived from DzProperty ). Those properties may be added and removed at runtime and may be specified as animatable or not. There are several types of properties that have been supplied with the Studio SDK. Property names must be unique within an element. A variety of methods are provided to allow easy traversal and/or searching of the properties list for an object. Methods are provided to clear animation data on all properties of an object either over a range of time, or over all time. DzElement takes ownership of all properties added via addProperty () and/or addPrivateProperty (). Subclasses should not attempt to delete properties that have been added to the element.
 */
declare class DzElement {
    elementID(): number;

    addDataItem(item: DzElementData): DzError;
    addPrivateProperty(prop: DzProperty): DzError;
    addProperty(prop: DzProperty): DzError;
    beginEdit(): void;
    cancelEdit(): void;
    clearAllAnimData(): void;
    clearAnimData(range: DzTimeRange): void;
    copyFrom(source: DzElement): void;
    copyToClipboard(contentTypes: any[]): elementclipboard_dz;
    deleteDataItem(item: DzElementData): DzError;
    findDataItem(dataName: string): DzElementData;
    findDataItemIndex(item: DzElementData): number;
    findMatchingProperty(srcProp: DzProperty): DzProperty;
    findPrivateProperty(name: string): DzProperty;
    findPrivateProperty(name: string, caseSensitive: boolean): DzProperty;
    findPrivatePropertyByLabel(label: string): DzProperty;
    findPrivatePropertyByLabel(label: string, caseSensitive: boolean): DzProperty;
    findProperty(name: string): DzProperty;
    findProperty(name: string, caseSensitive: boolean): DzProperty;
    findPropertyByLabel(label: string, caseSensitive: boolean): DzProperty;
    findPropertyByLabel(label: string): DzProperty;
    finishEdit(): void;
    getAttributes(settings: DzSettings): void;
    getDataItem(index: number): DzElementData;
    getDataItemList(): any[];
    getElementChild(which: number): DzElement;
    getElementParent(): DzElement;
    getLabel(): string;
    getLoadScript(): DzScript;
    getNameEditScope(): NameEditScope;
    getNumDataItems(): number;
    getNumElementChildren(): number;
    getNumPrivateProperties(): number;
    getNumProperties(): number;
    getPrivateProperty(index: number): DzProperty;
    getPrivatePropertyGroups(): DzPropertyGroupTree;
    getPrivatePropertyList(): any[];
    getProperty(index: number): DzProperty;
    getPropertyGroups(): DzPropertyGroupTree;
    getPropertyList(): any[];
    getTypeLabel(): string;
    getUniqueDataItemName(dataName: string): string;
    getUniquePrivatePropertyName(name: string): string;
    getUniquePropertyName(name: string): string;
    inEdit(): boolean;
    insertPrivateProperty(index: number, prop: DzProperty): DzError;
    insertProperty(index: number, prop: DzProperty): DzError;
    moveDataItemToIndex(item: DzElementData, index: number): DzError;
    movePrivateProperty(prop: DzProperty, element: DzElement): DzError;
    moveProperty(prop: DzProperty, element: DzElement): DzError;
    removeDataItem(item: DzElementData): DzError;
    removePrivateProperty(prop: DzProperty): DzError;
    removePrivateProperty(name: string): DzError;
    removeProperty(name: string): DzError;
    removeProperty(prop: DzProperty): DzError;
    setAttributes(settings: DzSettings): DzElement;
    setLabel(name: string): DzError;
    setLoadScript(script: DzScript): void;
    setName(name: string): void;
    shouldSortOnLoad(): boolean;
    update(): void;

    // SIGNALS
    labelChanged(newLabel: string): void;
    parentChanged(): void;
    privatePropertyAdded(prop: DzProperty): void;
    privatePropertyListChanged(): void;
    privatePropertyListInTreeChanged(): void;
    privatePropertyRemoved(prop: DzProperty): void;
    privatePropertyTreeChanged(): void;
    propertyAdded(prop: DzProperty): void;
    propertyListChanged(): void;
    propertyListInTreeChanged(): void;
    propertyRemoved(prop: DzProperty): void;
    propertyTreeChanged(): void;
}

/**
 * Implements a custom data item that allows named data to be associated with an element of the scene. See Also: DzElement :: addDataItem () DzElement :: removeDataItem () DzElement :: deleteDataItem () DzElement :: getNumDataItems () DzElement :: getDataItem () DzElement :: getDataItemList () DzElement :: getUniqueDataItemName () DzElement :: findDataItem () DzElement :: moveDataItemToIndex () DzElement :: findDataItemIndex ()
 */
declare class DzElementData {
    duplicate(owner: DzElement): DzElementData;
    getOwner(): DzElement;

    // SIGNALS
    addedToElement(owner: DzElement): void;
    elementDeleting(formerOwner: DzElement): void;
    removedFromElement(formerOwner: DzElement): void;
}

/**
 * Implements a custom data item that causes a specified file to be associated with the owning element after the element has been loaded into the scene. If the file to post-load is not a script, the path is stored but the file is not loaded. If the file to post-load is a script: A global transient variable named DataItem , which refers to the DzElementPostLoadFileData that invoked the execution of the script, is provided to the script in the global context at runtime. Attempts to use this global variable outside of the associated script will result in a ReferenceError . A global transient variable named FileIOSettings , which refers to the DzFileIOSettings that was used when the element that owns this data item was loaded, is provided to the script in the global context at runtime. Attempts to use this global variable outside of the associated script will result in a ReferenceError . (since 4.9.4.109) Attention: The differences between this implementation and DzSimpleElementScriptData are that this implementation can reference the file path of a file that is not a script and it does not have an associated DzSettings that can be used to configure said script. See Also: DzElement :: addDataItem () DzElement :: removeDataItem () DzElement :: deleteDataItem () DzElement :: getNumDataItems () DzElement :: getDataItem () DzElement :: getDataItemList () DzElement :: getUniqueDataItemName () DzElement :: findDataItem () DzElement :: moveDataItemToIndex () DzElement :: findDataItemIndex ()
 */
declare class DzElementPostLoadFileData {
    getPostLoadFilePath(): string;
    setPostLoadFilePath(script: string): void;
}

/**
 * This class provides an animatable enumerated property that is stored and can be accessed as an integer property. It maintains a list of strings that correspond to the integer value of the property.
 */
declare class DzEnumProperty {
    addItem(item: string, index: number): number;
    findItemString(str: string): number;
    getDefaultStringValue(): string;
    getItem(i: number): string;
    getKeyStringValue(i: number): string;
    getNumItems(): number;
    getRawStringValue(): string;
    getRawStringValue(tm: number): string;
    getStringValue(tm: number): string;
    getStringValue(): string;
    getUniqueItemString(item: string): string;
    removeAllItems(): void;
    removeItem(index: number): boolean;
    replaceItem(index: number, item: string): boolean;
    setItems(items: any[]): void;
    setValueFromString(str: string): boolean;
    setValueFromString(tm: number, str: string): boolean;

    // SIGNALS
    itemListChanged(): void;
}

/**
 * Provides a control that allows a user to adjust a bounded, enumerated, integer value. The slider is clamped by default, and automatically sets its min and max range according to the number of string values it contains.
 */
declare class DzEnumSlider {
    count(): number;
    text: string;

    addItem(label: string): number;
    clear(): void;
    getItem(index: number): string;
    moveItem(from: number, to: number): void;
    removeItem(index: number): void;
    renameItem(index: number, label: string): void;
}

/**
 * This utility class implements the logic of 'baking' (unlinking) the current state of a controller property on a node to the numeric properties it controls, such that the controlled properties remain at the respective values they were at in that moment of time. The DzERCLink between the 'baked' properties and the controller is removed. The controller property (the DzNumericProperty that does the controlling) must be set before calling doBake (); see setControllerProperty (). See Also: Sample: ERC Bake Attention: This object is provided by the Property Hierarchy plugin. It is only available when the Property Hierarchy plugin is activated and enabled. Since: 4.9.3.101
 */
declare class DzERCBake {
    doBake(): boolean;
    doBakeKeyed(warn: boolean): boolean;
    getControllerProperty(): DzNumericProperty;
    setControllerProperty(prop: DzNumericProperty): void;

    // SIGNALS
    ERCChanged(): void;
}

/**
 * This utility class implements the logic of 'freezing' (linking) the current state of numeric properties on a node (or multiple nodes) to a controller property, such that adjusting the controller property adjusts the linked properties in kind. The DzERCLink between the 'frozen' properties and the controller are created such that when the controller is set to the value it is at when the 'freeze' operation is performed, the 'frozen' properties will be at the respective values they were at in that moment of time. The controller node (the DzNode that the controlling property is located on) and the controller property (the DzNumericProperty that ultimately does the controlling) must be set before calling doFreeze (); see setControllerNode () and setControllerProperty (). An additional property can be set and used to attenuate the effect of the controller property on the 'frozen' properties, or have its value attenuated as the controller property is applied, depending on the AttenuateMode set. The addPropertiesToFreeze () method is used to inspect the current state of the numeric properties on a a given node that are not currently set to their respective raw values and add them to the list of those properties to be linked to the controller property. This list of properties can be inspected and/or modified using the getPropertiesToFreeze () and setPropertiesToFreeze () methods. See Also: Sample: ERC Freeze Attention: This object is provided by the Property Hierarchy plugin. It is only available when the Property Hierarchy plugin is activated and enabled. Since: 4.9.3.95
 */
declare class DzERCFreeze {
    addPropertiesToFreeze(node: DzNode): boolean;
    doFreeze(): boolean;
    getApplyController(): boolean;
    getAttenuateMode(): AttenuateMode;
    getAttenuateProperty(): DzNumericProperty;
    getControllerNode(): DzNode;
    getControllerProperty(): DzNumericProperty;
    getKeyed(): boolean;
    getPropertiesToFreeze(): any[];
    getRestoreFigure(): boolean;
    getRestoreRigging(): boolean;
    getRestoreSelectedItems(): boolean;
    setApplyController(yesNo: boolean): void;
    setAttenuateMode(mode: AttenuateMode): void;
    setAttenuateProperty(prop: DzNumericProperty): void;
    setControllerNode(node: DzNode): void;
    setControllerProperty(prop: DzNumericProperty): void;
    setKeyed(yesNo: boolean): void;
    setPropertiesToFreeze(propList: any[]): void;
    setRestoreFigure(yesNo: boolean): void;
    setRestoreRigging(yesNo: boolean): void;
    setRestoreSelectedItems(yesNo: boolean): void;

    // SIGNALS
    ERCChanged(): void;
}

/**
 * This numeric controller implements an algorithm that is based on the value of another property. There are six formulas which correspond to the ERCType of the object - the default ERCType is ERCDeltaAdd. The formulas are: ERCDeltaAdd: f(v) = v + (c * m) + a ERCDivideInto: f(v) = (c / v) + a ERCDivideBy: f(v) = (v / c) + a ERCMultiply: f(v) = (c * v) + a ERCSubtract: f(v) = v - c + a ERCAdd: f(v) = v + c + a ERCKeyed: f(v) = v + P© Where: v is the current (keyed) value of the property with the link c is the current (final) value of the property that the link is driven by m is an optional scalar multiplier a is an optional offset (additive) value. As an example of ERC in action, lets say that there are 3 properties A, B, and C. B is linked to A with a 'ERCDeltaAdd' DzERCLink with a multiplier of 1.0 and an additive value of 0.0. C is linked to B with a 'ERCDeltaAdd' DzERCLink with a multiplier of 2.0 and an additive value of 1.0. So, if the keyed value of A is 10.0, B is 0.0, and C is 0.0, the final values of the properties would be calculated as: A = 10.0 B = 0.0 + (10.0 * 1.0) + 0.0 = 10.0 C = 0.0 + (10.0 * 2.0) + 1.0 = 21.0 If B and C have keyed values - for example B is 5.0 and C is 2.0 - the final property values would be calculated as: A = 10.0 B = 5.0 + (10.0 * 1.0) + 0.0 = 15.0 C = 2.0 + (15.0 * 2.0) + 1.0 = 33.0
 */
declare class DzERCLink {
    active(): boolean;
    addend: number;
    autoOverride: boolean;
    isUserLink: boolean;
    keyInterpolation: ERCKeyInterpolation;
    saveWithOutput: boolean;
    scalar: number;
    type: ERCType;

    addKeyValue(key: number, value: number): number;
    addKeyValue(key: number, value: number, t: number, c: number, b: number): number;
    clearKeys(): void;
    duplicate(newProperty: DzNumericProperty): DzERCLink;
    findKeyIndex(key: number): number;
    getCurrentProperty(): DzNumericProperty;
    getKey(which: number): number;
    getKeyOpValue(val: number): number;
    getKeyParamB(which: number): number;
    getKeyParamC(which: number): number;
    getKeyParamT(which: number): number;
    getKeyValue(which: number): number;
    getNumKeyValues(): number;
    getProperty(): DzNumericProperty;
    presizeKeys(count: number): void;
    removeKeyValue(which: number): boolean;
    setProperty(prop: DzNumericProperty): void;

    // SIGNALS
    ercSourcePropertyRemoved(prop: DzProperty): void;
    keyChanged(which: number): void;
    keyInterpolationChanged(): void;
    keysListChanged(): void;
    propertyDeleted(prop: DzProperty): void;
    saveWithOutputChanged(): void;
    scalarChanged(): void;
    stageChanged(): void;
    typeChanged(): void;
}

/**
 * The base object for Errors reported by the script interpreter. This object can also be used in script to create user-generated errors.
 */
declare class Error {
    message(): string;
    name: string;
    fileName: string;
    lineNumber: string;

    toString(): string;
}

/**
 * 0x00000000 = DZ_NO_ERROR 0x00000050 = DZ_ALREADY_EXISTS_ERROR 0x00000051 = DZ_DOES_NOT_EXIST_ERROR 0x00000052 = DZ_NON_UNIQUE_NAME_ERROR 0x00000053 = DZ_ILLEGAL_HIERARCHY_ERROR 0x00000060 = DZ_ILLEGAL_ARGUMENT_ERROR 0x00000061 = DZ_ILLEGAL_OPERATION_ERROR 0x00000062 = DZ_OPERATION_FAILED_ERROR 0x00000063 = DZ_NO_MATCH_ERROR 0x00000064 = DZ_USER_CANCELLED_OPERATION 0x00000065 = DZ_UNHANDLED_EXCEPTION_ERROR 0x00000070 = DZ_TYPE_MISMATCH_ERROR 0x00000080 = DZ_SCRIPT_PARSE_ERROR 0x00000090 = DZ_MEMORY_ALLOCATION_ERROR 0x00000100 = DZ_PROFILE_NOT_SUPPORTED_ERROR 0x00000101 = DZ_ALREADY_BOUND_ERROR 0x00000102 = DZ_NOT_BOUND_ERROR 0x00000200 = DZ_UNABLE_TO_OPEN_FILE_ERROR 0x00000201 = DZ_SECTION_NOT_OPEN_ERROR 0x00000202 = DZ_SECTION_LENGTH_EXCEEDED_ERROR 0x00000203 = DZ_FORMAT_NOT_SUPPORTED_ERROR 0x00000204 = DZ_FILE_FORMAT_ERROR Note: You can use Global :: getErrorMessage () to convert an error code into a user-readable string.
 */
declare class DzError {
    valueOf(): number;
}

/**
 * This error is thrown by the interpreter when the global function eval() is used in a way that is incompatible with its definition. See the ECMA script specification for more information.
 */
declare class EvalError {
}

/**
 * Since: 4.10.0.101
 */
declare class DzEventScriptAction {
}

/**
 * TODO: Add detailed description.
 */
declare class DzExporter {
    getDescription(): string;
    getExtension(): string;
    isFileExporter(): boolean;
    writeFile(filename: string): DzError;
    writeFile(filename: string, options: DzFileIOSettings): DzError;
}

/**
 * There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getExportMgr (). See Also: Global :: App Samples: Exporters
 */
declare class DzExportMgr {
    canExport(filename: string): boolean;
    findExporter(filename: string): DzExporter;
    findExporterByClassName(className: string): DzExporter;
    findExporterIndex(filename: string): number;
    getExporter(exporterIdx: number): DzExporter;
    getNumExporters(): number;
    makeExportFileFilter(filter: DzFileFilter, defaultFilter: string): void;
    exportFile(fileName: string, exporterIdx: number): DzError;
    exportFile(fileName: string, exporterIdx: number, options: DzFileIOSettings): DzError;
    getExportPath(): string;
    isExporting(): boolean;
    setExportPath(path: string): void;

    // SIGNALS
    fileExported(): void;
    fileExportStarting(): void;
}

/**
 * Represents a list of faces from a geometry that are collected into a group. The group is stored as a list of integers which are indices into the face list of the geometry which this group references. See Also: DzFacetMesh :: getNumFaceGroups () DzFacetMesh :: getFaceGroup () DzFacetMesh :: findFaceGroup ()
 */
declare class DzFaceGroup {
}

/**
 * A 3 or 4 sided polygonal face within a polygon mesh. See Also: DzFacetMesh
 */
declare class DzFacet {
    cageIndex(): number;
    edgeIdx1: number;
    edgeIdx2: number;
    edgeIdx3: number;
    edgeIdx4: number;
    faceGroupIndex: number;
    materialIndex: number;
    normIdx1: number;
    normIdx2: number;
    normIdx3: number;
    normIdx4: number;
    uvwIdx1: number;
    uvwIdx2: number;
    uvwIdx3: number;
    uvwIdx4: number;
    vertIdx1: number;
    vertIdx2: number;
    vertIdx3: number;
    vertIdx4: number;

    clear(): void;
    clearTriFanCount(): void;
    clearTriFanRoot(): void;
    getTriFanCount(): number;
    getTriFanEdgeCount(): number;
    getTriFanMaxEdgeIdx(): number;
    getTriFanOffset(): number;
    getTriFanRoot(): number;
    isQuad(): boolean;
    isTri(): boolean;
    isTriFan(): boolean;
    isTriFanChild(): boolean;
    isTriFanRoot(): boolean;
    setTriFanCount(count: number): void;
    setTriFanRoot(rootIdx: number): void;
    toString(): string;
}

/**
 * This facet mesh handles polygons in a general manner. DAZ Studio converts all higher order polygons to triangles and quadrangles.
 */
declare class DzFacetMesh {
    assetAuthor(): DzAuthor;
    assetFileRevision: DzVersion;
    assetId: string;
    assetIdAliases: any[];
    assetModifiedDate: Date;
    assetNeedSave: boolean;
    assetSource: DzUri;
    assetUri: DzUri;
    extendedAssetIds: string;
    nameAliases: any[];

    getInfiniteSharpValueWeightValue(): number;
    getOpenSubdivVersion(): string;
    activateFaceGroup(name: string): number;
    activateFaceGroup(index: number): void;
    activateMaterial(name: string): number;
    activateMaterial(index: number): void;
    addFacet(vertIndices: any[], uvIndices: any[], flags: number): void;
    addFacet(facetIn: DzFacet, pTex: number, flags: number): void;
    addPolyline(vertexIndices: any[], uvIndices: any[], flags: number): void;
    addPolylineRootSegment(vertIdx1: number, vertIdx2: number, flags: number): void;
    addPolylineRootSegment(vertIdx1: number, vertIdx2: number, uvIdx1: number, uvIdx2: number, flags: number): void;
    addSegmentToLastPolyline(vertexIndex: number): void;
    addSegmentToLastPolyline(vertexIndex: number, uvIndex: number): void;
    addUVSet(uvSet: DzUVSet): void;
    applyFullSmoothing(): void;
    applySmoothing(angle: number): void;
    applyUVSet(uvSet: DzUVSet): void;
    clearWeightedEdges(): void;
    clearWeightedVertices(): void;
    createFaceGroup(name: string): boolean;
    createMaterialGroup(name: string): number;
    findFaceGroup(name: string): DzFaceGroup;
    findMaterialGroup(name: string): DzMaterialFaceGroup;
    findUVSetIndexByLabel(label: string): number;
    getCurrentSubDivisionLevel(): number;
    getEdge(index: number): DzEdge;
    getEdgeWeight(vertIdxA: number, vertIdxB: number): number;
    getFaceGroup(index: number): DzFaceGroup;
    getFacet(index: number): DzFacet;
    getMaterialGroup(index: number): DzMaterialFaceGroup;
    getNormal(index: number): DzVec3;
    getNumEdges(): number;
    getNumFaceGroups(): number;
    getNumFacets(): number;
    getNumMaterialGroups(): number;
    getNumNormals(): number;
    getNumPolylines(): number;
    getNumPolylineSegments(): number;
    getNumQuads(): number;
    getNumTris(): number;
    getNumWeightedEdges(): number;
    getNumWeightedVertices(): number;
    getPolylineCageIndex(polylineIdx: number): number;
    getPolylineFaceGroupIndex(polylineIdx: number): number;
    getPolylineMaterialGroupIndex(polylineIdx: number): number;
    getPolylineUVIndices(index: number): any[];
    getPolylineVertexIndices(index: number): any[];
    getSubDAlgorithm(): SubDAlgorithm;
    getSubDEdgeInterpolation(): SubDEdgeInterpolation;
    getSubDNormalSmoothingMode(): SubDNormalSmoothingMode;
    getVertexWeight(vertIdx: number): number;
    getWeightedEdges(): any[];
    getWeightedVertices(): any[];
    insertUVSet(idx: number, uvSet: DzUVSet): void;
    preSizeFacets(numFacets: number): DzError;
    preSizePolylines(numPolyLines: number, numTotalSegments: number): DzError;
    preSizeWeightedEdges(numEdges: number): void;
    preSizeWeightedVertices(numVerts: number): void;
    removeAllFacets(removeMats: boolean, removeGroups: boolean): void;
    removeAllFacets(): void;
    removeAllPolylines(removeMats: boolean, removeGroups: boolean): void;
    removeAllUVSets(): void;
    removeFaceGroup(name: string, defaultGrp: string): DzError;
    removeFacet(facetIdx: number): void;
    removeFacets(grp: DzFaceGroup, removeVerts: boolean): void;
    removeMaterialGroup(removeIdx: number, defaultGrpIdx: number, shape: DzShape): DzError;
    removePolyline(polylineIdx: number): void;
    removeUVSet(index: number): void;
    removeUVSet(uvSet: DzUVSet): void;
    setEdgeWeight(vertIdxA: number, vertIdxB: number, weight: number): void;
    setNumPolylines(numPolyLines: number, numTotalSegments: number): void;
    setSubDAlgorithm(algo: SubDAlgorithm): void;
    setSubDEdgeInterpolation(interp: SubDEdgeInterpolation): void;
    setSubDNormalSmoothingMode(normalMode: SubDNormalSmoothingMode): void;
    setUVList(map: DzMap): void;
    setVertexWeight(vertIdx: number, weight: number): void;

    // SIGNALS
    assetModified(): void;
    assetWasSaved(): void;
    edgeSelectionChanged(): void;
    facetSelectionChanged(): void;
    polylineSelectionChanged(): void;
    subDivisionEnabled(onOff: boolean): void;
    uvListChanged(): void;
}

/**
 * No description available.
 */
declare class DzFacetShape {
    getFacetMesh(): DzFacetMesh;
    getLODControl(): DzEnumProperty;
    getSubDAlgo(): number;
    getSubDAlgorithmControl(): DzEnumProperty;
    getSubDDrawLevel(): number;
    getSubDInterpolateLevel(): number;
    getSubDInterpolateLevelControl(): DzEnumProperty;
    getSubDLevelControl(): DzIntProperty;
    getSubDRenderLevel(): number;
    getSubDRenderLevelControl(): DzIntProperty;
    isLodActive(): boolean;
    isSubDivisionActive(): boolean;
    subDMesh(mesh: DzFacetMesh, isRender: boolean): void;

    // SIGNALS
    facetMeshChanged(): void;
    renderSubDChanged(): void;
    subDAlgorithmChanged(): void;
    subDInterpolateLevelChanged(): void;
    subDNormalSmoothingChanged(): void;
}

/**
 * A specialization of DzExporter that implements an exporter for the Autodesk FBX (.fbx) format. See Also: DzExportMgr :: findExporterByClassName () DzExportMgr :: findExporter () Sample: Silent FBX Export
 */
declare class DzFbxExporter {
}

/**
 * A specialization of DzImporter that implements an importer for the Autodesk FBX (.fbx) format. Through its use of the FBX SDK to accomplish this task, this importer also provides import capabilities for the Autodesk AutoCAD DXF (.dxf) format, the Autodesk 3ds Max (.3ds) format, and the Collada DAE (.dae) format, as supported by the FBX SDK. Attention: The FBX SDK also provides import capabilities for the Alias Wavefront OBJ (.obj) format, but it has been intentionally excluded. Use DzObjImporter instead. See Also: DzImportMgr :: findImporterByClassName () DzImportMgr :: findImporter () Sample: Silent FBX Import
 */
declare class DzFbxImporter {
}

/**
 * A specialization of DzSkeleton that represents a figure where the associated geometry is bound to its bones using a set of weight maps. When serving the role of “follower”, this type of figure supports “culling” (hiding) facets in the geometry of another figure (i.e., a “follow target”). This can be useful for purposes of hiding areas of an underlying figure to mitigate occurrences of “poke-through” (visible intersection of meshes), where an inner-layer mesh is revealed through an outer-layer mesh. Further, this type of figure also supports “grafting” (integrating) its geometry into the geometry of another figure (i.e., a “follow target”). In horticultural terms, the “follower” serves the role of “scion” and the “follow target” serves the role of “stock.” “Grafting” between the geometries of figures relies on them each having vertices that are exactly coincident in their respective base shapes. “Culling” can be used to create an open edge in the “stock” that matches an open edge in the “scion” in order to establish a “graft” that blends smoothly, when a “follower” is assigned a “follow target.” See Also: DzSkinBinding DzBoneBinding DzConditionalGraftModifier
 */
declare class DzFigure {
    convertPropToFigure(srcNode: DzNode, rootBoneName: string, localMaps: boolean, inheritSkeleton: boolean): DzFigure;
    addFollowTargetHiddenFace(faceIdx: number): void;
    addWeldPoint(followerIdx: number, targetIdx: number, notifyChange: boolean): void;
    clearFollowTargetHiddenFaces(): void;
    clearWeldPoints(): void;
    getCullFigure(which: number): DzFigure;
    getFollowerWeldIndex(which: number): number;
    getFollowTargetFaceCount(): number;
    getFollowTargetVertexCount(): number;
    getFollowTargetWeldIndex(which: number): number;
    getGraftFigure(which: number): DzFigure;
    getNumCullFigures(): number;
    getNumFollowTargetHiddenFaces(): number;
    getNumGraftFigures(): number;
    getNumWeldPoints(): number;
    getSkinBinding(): DzSkinBinding;
    isGraftFollowing(): boolean;
    mergeFollowers(): DzError;
    optimizeWeldPoints(): void;
    presizeFollowTargetHiddenFaces(num: number): void;
    presizeWeldPoints(num: number): void;
    removeDuplicateWeldPoints(): void;
    removeWeldPoint(which: number): void;
    setFollowTargetFaceCount(num: number): void;
    setFollowTargetVertexCount(num: number): void;
    willGraftInDraw(): boolean;
    willGraftInRender(settings: DzRenderSettings): boolean;

    // SIGNALS
    followTargetHiddenListChanged(): void;
    graftListChanged(): void;
    weldListChanged(): void;
}

/**
 * Provides access for reading and writing files.
 */
declare class DzFile {
    close(): void;
    copy(newName: string): boolean;
    eof(): boolean;
    error(): FileError;
    errorString(): string;
    isOpen(): boolean;
    isTextModeEnabled(): boolean;
    link(linkName: string): boolean;
    open(mode: OpenMode): boolean;
    openMode(): OpenMode;
    peek(maxSize: number): ByteArray;
    pos(): number;
    read(maxSize: number): ByteArray;
    read(): string;
    readAll(): ByteArray;
    readByte(): number;
    readByteLine(maxSize: number): ByteArray;
    readLine(): string;
    readLines(): any[];
    rename(newName: string): boolean;
    reset(): boolean;
    seek(pos: number): boolean;
    setFileName(name: string): void;
    setPermissions(permissions: Permissions): boolean;
    setTextModeEnabled(enabled: boolean): void;
    write(data: string, maxSize: number): number;
    writeByte(byte: number): void;
    writeBytes(byteArray: ByteArray): number;
    writeLine(data: string): void;
    writeLineUtf8(data: string): void;
    writeUtf8(data: string, length: number): number;
}

/**
 * A global static object available via the Global :: FileDialog variable. This object provides functions that display OS native file dialogs to the user.
 */
declare class DzFileDialog {
    doAudioClipOpenDialog(startWith: string, parent: DzWidget): string;
    doDirectoryDialog(title: string, desc: string, parent: DzWidget): string;
    doDirectoryDialog(title: string, desc: string, startWith: string, parent: DzWidget): string;
    doFileDialog(open: boolean, title: string, startWith: string, filter: string, selectedFilter: number, parent: DzWidget): string;
    doImageDialog(open: boolean, startWith: string, parent: DzWidget): string;
    doVideoClipSaveDialog(startWith: string, parent: DzWidget): string;
    getOpenFileNames(dir: string, filter: string, title: string, parent: DzWidget): any[];
}

/**
 * For each group of files that you want to make available to the user, create a new filter with the newFilter () call, then add one or more file extensions to be accepted by the filter.
 */
declare class DzFileFilter {
    addExtension(extension: string): void;
    addExtensions(extensions: any[]): void;
    getDefaultFilter(): number;
    getExtension(filterIdx: number, extensionIdx: number): string;
    getFilterDescription(filterIdx: number): string;
    getNumExtensions(filterIdx: number): number;
    getNumFilters(): number;
    newFilter(description: string): void;
    setDefaultFilter(filterIdx: number): void;
}

/**
 * Provides access to getting information about files. It also serves as the base class for the other DAZ Script File I/O types.
 */
declare class DzFileInfo {
    absoluteDir(): DzDir;
    absoluteFilePath(): string;
    absolutePath(): string;
    bundleName(): string;
    caching(): boolean;
    canonicalFilePath(): string;
    canonicalPath(): string;
    completeBaseName(): string;
    completeSuffix(): string;
    created(): Date;
    dir(): DzDir;
    exists(): boolean;
    fileName(): string;
    filePath(): string;
    isAbsolute(): boolean;
    isBundle(): boolean;
    isDir(): boolean;
    isExecutable(): boolean;
    isFile(): boolean;
    isHidden(): boolean;
    isReadable(): boolean;
    isRelative(): boolean;
    isRoot(): boolean;
    isSymLink(): boolean;
    isWritable(): boolean;
    lastModified(): Date;
    lastRead(): Date;
    makeAbsolute(): boolean;
    path(): string;
    permission(permissions: Permissions): boolean;
    permissions(): Permissions;
    refresh(): void;
    remove(): boolean;
    setCaching(enable: boolean): void;
    setFile(file: string): void;
    setFile(dir: DzDir, file: string): void;
    setFile(file: DzFile): void;
    size(): number;
    sizeStr(): string;
    suffix(): string;
    symLinkTarget(): string;
    absFileName(): string;
    extension(): string;
    baseName(): string;
}

/**
 * This class provides functionality common to all file importers and exporters such as the ability to edit options before file import/export. Also, this class provides functions for importers/exporters to report errors to the user/log file, and provides static convenience functions for dissecting file paths into their parts.
 */
declare class DzFileIO {
    optionsShown(): boolean;

    getDefaultOptions(options: DzFileIOSettings): void;
    getOptions(options: DzFileIOSettings, useInterface: boolean, filename: string): boolean;
    showOptions(): boolean;
}

/**
 * Responsible for managing presets in the form of DzFileIOSettings objects for various importers, exporters, and other forms of file I/O. There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getFileIOPresetMgr (). File I/O presets are defined by a unique name. They have two types of settings: Specific Settings and Common Settings. Specific Settings Specific settings are tied to a class name. This class name is typically, but not always, the name of an importer or exporter, such as “DzObjImporter” or “DzObjExporter.” The key values for specific settings will vary based on the class. Common Settings Common settings for a preset are common to all class names. These include settings that define scale values and axis settings. Common keys can be accessed via the following methods: getLateralAxisKey () getVerticalAxisKey () getDepthAxisKey () getInvertLateralAxisKey () getInvertVerticalAxisKey () getInvertDepthAxisKey () getScaleKey () The scale value used by the presets is for importers. If you are working with an exporter then the scale value needs to be converted to 1/scale. As an example, if the scale value for a preset is 2.54 then the scale value for an exporter would be 1/2.54 = 0.3937
 */
declare class DzFileIOPresetMgr {
    getAllCurrentSettings(className: string, settings: DzFileIOSettings): boolean;
    getAllDefaults(className: string, settings: DzFileIOSettings): boolean;
    getAllSettings(presetName: string, className: string, settings: DzFileIOSettings): boolean;
    getAvailableClasses(presetName: string): any[];
    getAvailablePresets(className: string): any[];
    getCommonApplicationDefaults(settings: DzFileIOSettings): void;
    getCommonDefaults(className: string, settings: DzFileIOSettings): boolean;
    getCommonSettings(presetName: string, className: string, settings: DzFileIOSettings): boolean;
    getCurrentCommonSettings(className: string, settings: DzFileIOSettings): boolean;
    getCurrentSpecificSettings(className: string, settings: DzFileIOSettings): boolean;
    getCustomPresetLabel(): string;
    getDepthAxisKey(): string;
    getInvertDepthAxisKey(): string;
    getInvertLateralAxisKey(): string;
    getInvertVerticalAxisKey(): string;
    getLateralAxisKey(): string;
    getPresetID(presetName: string, className: string): number;
    getPresetName(id: number, className: string): string;
    getScaleKey(): string;
    getSpecificDefaults(className: string, settings: DzFileIOSettings): boolean;
    getSpecificSettings(presetName: string, className: string, settings: DzFileIOSettings): boolean;
    getSystemPresets(className: string): any[];
    getUserPresets(className: string): any[];
    getVerticalAxisKey(): string;
    isSystemPreset(presetName: string): boolean;
    isUserPreset(presetName: string): boolean;
    presetExists(id: number, className: string): boolean;
    presetExists(presetName: string, className: string): boolean;
    removeUserPreset(presetName: string, className: string): boolean;
    saveUserPreset(presetName: string, className: string, keepCommonSettings: boolean, settings: DzFileIOSettings): boolean;

    // SIGNALS
    presetAdded(presetName: string, className: string): void;
    presetLoadFinished(): void;
    presetRemoved(presetName: string, className: string): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzFileIOSettings {
}

/**
 * Attention: Attempts to save and restore as relative path when possible.
 */
declare class DzFileProperty {
    getAbsolutePath(path: string): string;
    getDisplayText(): string;
    getFilter(): string;
    getType(): FileType;
    loadFile(): boolean;
    setDisplayText(text: string): void;
    setFilter(filter: string): void;
    setType(type: FileType): void;

    // SIGNALS
    displayTextChanged(): void;
    filterChanged(): void;
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureComponent instead.
 */
declare class DzFlipManip {
    flipHorizontal(): boolean;
    flipVertical(): boolean;
    setFlipHorizontal(onOff: boolean): void;
    setFlipVertical(onOff: boolean): void;
}

/**
 * This class provides an animatable floating-point property with 2 values that is stored and can be accessed as a DzVec2 . Since: 4.6.4.88
 */
declare class DzFloat2Property {
    adjustFloat2Value(val: DzVec2): DzVec2;
    adjustFloat2Value(tm: number, val: DzVec2): DzVec2;
    getDefaultFloat2Value(): DzVec2;
    getFloat2FollowValue(): DzVec2;
    getFloat2FollowValue(tm: number): DzVec2;
    getFloat2Value(): DzVec2;
    getFloat2Value(tm: number): DzVec2;
    getKeyFloat2Value(i: number): DzVec2;
    getLocalFloat2Value(): DzVec2;
    getLocalFloat2Value(tm: number): DzVec2;
    getRawFloat2Value(tm: number): DzVec2;
    getRawFloat2Value(): DzVec2;
    setDefaultFloat2Value(val: DzVec2): void;
    setFloat2Value(tm: number, val: DzVec2): void;
    setFloat2Value(val: DzVec2): void;
    setFloat2Value(tm: number, val: DzVec2, interp: InterpolationType): void;
    setFloat2Value(tm: number, valIn: DzVec2, interp: InterpolationType, param0: number, param1: number, param2: number): void;
    setKeyFloat2Value(i: number, val: DzVec2): void;
}

/**
 * This class provides an animatable floating-point property with 3 values that is stored and can be accessed as a DzVec3 . Since: 4.6.4.88
 */
declare class DzFloat3Property {
    adjustFloat3Value(val: DzVec3): DzVec3;
    adjustFloat3Value(tm: number, val: DzVec3): DzVec3;
    getDefaultFloat3Value(): DzVec3;
    getFloat3FollowValue(): DzVec3;
    getFloat3FollowValue(tm: number): DzVec3;
    getFloat3Value(): DzVec3;
    getFloat3Value(tm: number): DzVec3;
    getKeyFloat3Value(i: number): DzVec3;
    getLocalFloat3Value(): DzVec3;
    getLocalFloat3Value(tm: number): DzVec3;
    getRawFloat3Value(tm: number): DzVec3;
    getRawFloat3Value(): DzVec3;
    setDefaultFloat3Value(val: DzVec3): void;
    setFloat3Value(tm: number, val: DzVec3): void;
    setFloat3Value(val: DzVec3): void;
    setFloat3Value(tm: number, val: DzVec3, interp: InterpolationType): void;
    setFloat3Value(tm: number, valIn: DzVec3, interp: InterpolationType, param0: number, param1: number, param2: number): void;
    setKeyFloat3Value(i: number, val: DzVec3): void;
}

/**
 * This class manages 4-component colors (colors that can include an alpha value).
 */
declare class DzFloatColor {
    alpha(): string;
    blue: string;
    green: string;
    red: string;

    clamp(min: number, max: number, includeAlpha: boolean): void;
    clamped(min: number, max: number, includeAlpha: boolean): DzFloatColor;
    clampedMax(max: number, includeAlpha: boolean): DzFloatColor;
    clampedMin(min: number, includeAlpha: boolean): DzFloatColor;
    clampMax(max: number, includeAlpha: boolean): void;
    clampMin(min: number, includeAlpha: boolean): void;
    equals(color: DzFloatColor, tolerance: number): boolean;
    gammaColor(gamma: number, doAlpha: boolean): void;
    getColor(): { r: number, g: number, b: number, a: number };
    getGrayscale(): number;
    getHsl(): any[];
    getHsv(): any[];
    getMaxRGBValue(): number;
    getRelativeLuminance(): number;
    getRgba(): any[];
    linearizeColor(gamma: number, doAlpha: boolean): void;
    modulate(min: number, max: number, includeAlpha: boolean): DzFloatColor;
    modulo(min: number, max: number, includeAlpha: boolean): void;
    setHsl(h: number, s: number, l: number, a: number): void;
    setHsl(list: any[]): void;
    setHsv(list: any[]): void;
    setHsv(h: number, s: number, v: number, a: number): void;
    setRgba(list: any[]): void;
    setValue(r: number, g: number, b: number, a: number): void;
    setValue(color: { r: number, g: number, b: number, a: number }): void;
    toString(): string;
}

/**
 * This class provides an animatable color property that is stored and can be accessed as a floating point values. Since: 4.6.4.85
 */
declare class DzFloatColorProperty {
    adjustFloatColorValue(val: DzFloatColor): DzFloatColor;
    adjustFloatColorValue(tm: number, val: DzFloatColor): DzFloatColor;
    getDefaultFloatColorValue(): DzFloatColor;
    getFloatColorFollowValue(): DzFloatColor;
    getFloatColorFollowValue(tm: number): DzFloatColor;
    getFloatColorValue(): DzFloatColor;
    getFloatColorValue(tm: number): DzFloatColor;
    getFloatMax(): number;
    getFloatMin(): number;
    getFloatSensitivity(): number;
    getKeyFloatColorValue(i: number): DzFloatColor;
    getLocalFloatColorValue(): DzFloatColor;
    getLocalFloatColorValue(tm: number): DzFloatColor;
    getRawFloatColorValue(tm: number): DzFloatColor;
    getRawFloatColorValue(): DzFloatColor;
    setDefaultFloatColorValue(val: DzFloatColor): void;
    setFloatColorValue(val: DzFloatColor): void;
    setFloatColorValue(tm: number, val: DzFloatColor, interp: InterpolationType, param0: number, param1: number, param2: number): void;
    setFloatColorValue(tm: number, val: DzFloatColor, interp: InterpolationType): void;
    setFloatColorValue(tm: number, val: DzFloatColor): void;
    setFloatMax(max: number): void;
    setFloatMin(min: number): void;
    setFloatMinMax(min: number, max: number): void;
    setFloatSensitivity(sens: number): void;
    setKeyFloatColorValue(i: number, val: DzFloatColor): void;
    setRawFloatColorValue(tm: number, val: DzFloatColor): void;
    setRawFloatColorValue(val: DzFloatColor): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzFloatProperty {
    add(val: number, applyToDefault: boolean): void;
    adjustValue(val: number): number;
    adjustValue(tm: number, val: number): number;
    divide(val: number, applyToDefault: boolean): void;
    getDefaultValue(): number;
    getDisplayAsPercent(): boolean;
    getKeyValue(i: number): number;
    getLocalValue(): number;
    getLocalValue(tm: number): number;
    getMax(): number;
    getMin(): number;
    getRawValue(): number;
    getRawValue(tm: number): number;
    getSensitivity(): number;
    getTransformType(): TransformType;
    getValue(): number;
    getValue(tm: number): number;
    multiply(val: number, applyToDefault: boolean): void;
    setDefaultValue(val: number): void;
    setDisplayAsPercent(onOff: boolean): void;
    setKeyValue(i: number, val: number): void;
    setMax(max: number): void;
    setMin(min: number): void;
    setMinMax(min: number, max: number): void;
    setSensitivity(sens: number): void;
    setTransformType(type: TransformType): void;
    setValue(tm: number, val: number, interp: InterpolationType, param0: number, param1: number, param2: number): void;
    setValue(val: number): void;
    setValue(tm: number, val: number, interp: InterpolationType): void;
    setValue(tm: number, val: number): void;
    subtract(val: number, applyToDefault: boolean): void;

    // SIGNALS
    displayAsPercentChanged(): void;
}

/**
 * Provides a control that allows a user to adjust a bounded floating point value.
 */
declare class DzFloatSlider {
    defaultValue(): number;
    displayAsPercent: boolean;
    indeterminate: boolean;
    max: number;
    min: number;
    sensitivity: number;
    value: number;

    // SIGNALS
    editCancelled(): void;
    valueChanged(value: number): void;
}

/**
 * The “Folder” container type serves to present assets as the files they represent exist in the folder structure on disk. See Also: DzAssetMgr :: getContentDirs () DzAssetMgr :: getPoserDirs () DzAssetMgr :: getImportDirs () DzAsset
 */
declare class DzFolderAssetContainer {
    excludeFolders(): any[];
    fileFilters: any[];
    isImport: boolean;
    isImportTopLevel: boolean;
    isNative: boolean;
    isNativeTopLevel: boolean;
    isPoser: boolean;
    isPoserIntermediate: boolean;
    isPoserTopLevel: boolean;
    onlyIncludeFolders: any[];

    fileMatchesFilter(shortFileName: string): boolean;
    getFullPath(): string;
    hasDirectoryChildren(): boolean;
    insertsAsLink(asset: DzAsset): boolean;
    updateChildren(): boolean;
}

/**
 * When a figure is “Fit to” (set to follow) another figure in the scene, the application uses a name-matching mechanism referred to as “Auto Follow” to establish relationships between properties in the following figure to the corresponding properties in the follow target. This relationship causes certain matched properties on the follower to inherit the values of the properties on the follow target. Active morphs on the follow target, when configured to “Auto Follow,” are projected from the follow target to the follower at the moment the follower is “Fit to” the follow target; this projection only occurs if a morph target bearing the same name does not already exist on the follower. Morphs that are configured to “Auto Follow” on the follow target that were not active at the moment the follower was “Fit to” the follow target are projected as they become active. These options are used to control how (or even if) “Auto Follow” morphs are projected. Each figure owns its own instance of this object. To modify the projection options for a follower, request the object from the figure and configure its instance rather than attempting to construct a new instance. See Also: DzSkeleton :: getFollowingProjectionOptions () Since: 4.8.1.86
 */
declare class DzFollowingProjectionOptions {
    adaptiveTolerance(): number;
    considerLinesAsRigid: boolean;
    disableMorphProjection: boolean;
    distanceSquaredTolerance: number;
    followerProjectionMorph: string;
    nearnessFactor: number;
    smartLeftRightHandling: boolean;
    sourceSubdivisionMode: SourceSubdivisionMode;
    useNear: boolean;
    uvSpaceProjection: boolean;
    vertexFirstProjection: boolean;
    writtenAsDefinition: boolean;

    addCorrelatedMorph(srcMorph: string, followerMorph: string): void;
    clearCorrelatedMorphs(): void;
    copyFrom(other: DzFollowingProjectionOptions): void;
    getFollowerCorrelatedMorph(which: number): string;
    getNumCorrelatedMorphs(): number;
    getSourceCorrelatedMorph(which: number): string;
    isAtDefault(): boolean;
    removeCorrelatedMorph(which: number): void;
}

/**
 * This is the script counterpart to the QFont type used in the C++ SDK. Attention: Inheritance will change to Object in a pending update.
 */
declare class Font {
    bold(): boolean;
    family: string;
    italic: boolean;
    pixelSize: number;
    pointSize: number;
    strikeout: boolean;
    underline: boolean;

    boundingRect(maxRect: Rect, text: string, flags: number): Rect;
    elidedText(text: string, mode: TextElideMode, width: number, flags: number): string;
    families(): any[];
    pointSizes(family: string, style: string): any[];
    size(text: string, flags: number): Size;
    styles(family: string): any[];
}

/**
 * Examples: See Also: Sample: Version Conversion Signals and Slots Signal to Function Connections Signal to Member Function Connections Signal to Named Member Function Connections Disconnecting
 */
declare class Function {
    arguments(): any[];
    length: number;

    apply(thisArg: any, argArray: any[]): any;
    bind(thisArg: any, ...args: any[]): void;
    call(thisArg: any, ...args: any[]): any;
    toString(): string;
    connect(receiver: any, _function: string): void;
    connect(functionRef: Function): void;
    disconnect(receiver: any, _function: string): void;
    disconnect(functionRef: Function): void;
    scriptConnect(receiver: any, _function: string): void;
    scriptConnect(functionRef: Function): void;
    scriptDisconnect(receiver: any, _function: string): void;
    scriptDisconnect(functionRef: Function): void;
}

/**
 * The base class for all mesh and geometry objects that can be referenced by DzShape , passed through the geometry pipeline, and drawn in the 3d view.
 */
declare class DzGeometry {
    hasPendingChanges(): boolean;

    getCurrentGeometryForNode(node: DzNode): DzGeometry;
    beginEdit(enableUndo: boolean): void;
    cancelEdit(): void;
    copyFrom(mesh: DzVertexMesh, shareVerts: boolean, shareFacets: boolean): boolean;
    finishEdit(): void;
    getBoundingBox(): DzBox3;
    getGroupBoundingBox(groupName: string, transform: DzMatrix3): DzBox3;
    getGroupBoundingBox(groupName: string): DzBox3;
    getGroupOrientedBox(groupName: string, transform: DzMatrix3, pos: DzVec3, rot: DzQuat, scale: DzVec3): DzOrientedBox3;
    getGroupOrientedBox(groupName: string, pos: DzVec3, rot: DzQuat, scale: DzVec3): DzOrientedBox3;
    getNumUVSets(): number;
    getNumVertices(): number;
    getOrientedBox(pos: DzVec3, rot: DzQuat, scale: DzVec3): DzOrientedBox3;
    getUniqueId(): number;
    getUVs(): DzMap;
    getUVSet(which: number): DzUVSet;
    isEmpty(): boolean;
    isRuntimeGenerated(): boolean;
    rotate(rot: DzQuat): void;
    scale(vec: DzVec3): void;
    scale(scalar: number): void;
    transform(matrix: DzMatrix3): void;
    translate(vec: DzVec3): void;

    // SIGNALS
    needRebuild(onOff: boolean): void;
    visibilityChanged(): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzGeometryImporter {
}

/**
 * A geometry shell is used to create a single (heavy) clone of a DzNode (subclass) in the scene that has a DzObject . This clone contains a deep copy of the world space geometry of the target node with its own unique materials. See Also: DzNode :: getObject () DzInstanceNode
 */
declare class DzGeometryShellNode {
    findFacetGroupVisibilityControl(group: DzFaceGroup): DzBoolProperty;
    findFacetGroupVisibilityControl(name: string): DzBoolProperty;
    findMaterialGroupVisibilityControl(name: string): DzBoolProperty;
    findMaterialGroupVisibilityControl(material: DzMaterial): DzBoolProperty;
    getShellNodeControl(): DzNodeProperty;
    getTarget(): DzNode;
}

/**
 * The DzGeometryUtil object provides access to geometry manipulation utility functions. It is accessible via the Global :: Geometry variable.
 */
declare class DzGeometryUtil {
    convertToSubD(node: DzNode, defaultLevel: number): DzError;
    createPrimitive(settings: DzSettings): DzNode;
    getDefaultPrimitiveOptions(type: PrimitiveType, settings: DzSettings): void;
}

/**
 * Implements a custom data item that stores the source file path and group name for the geometry of an imported object on the element. Can be used as follows to retrieve the path of the file from which a geometry was loaded:
 */
declare class DzGeomSourceFileData {
    groupName(): string;
}

/**
 * The global object is never used directly, and cannot be created using the new operator. It is automatically created when the scripting engine is initialized, and its functions and properties are available immediately. The global object has no syntax. Its functions and properties are accessed directly.
 */
declare class Global {
    false(): boolean;
    Infinity: number;
    JSON: JSON;
    Math: Math;
    NaN: number;
    null: any;
    true: boolean;
    undefined: Undefined;
    App: DzApp;
    ColorDialog: DzColorDialog;
    FileDialog: DzFileDialog;
    Geometry: DzGeometryUtil;
    MainWindow: DzMainWindow;
    MessageBox: DzMessageBox;
    OpenGL: DzOpenGL;
    Scene: DzScene;
    System: DzSystem;
    UndoStack: DzUndoStack;

    decodeURI(encodedURI: string): string;
    decodeURIComponent(encodedURIComponent: string): string;
    encodeURI(uri: string): string;
    encodeURIComponent(uriComponent: string): string;
    eval(str: string): any;
    isFinite(expression: any): boolean;
    isNaN(expression: any): boolean;
    parseFloat(str: string): number;
    parseInt(str: string, radix: number): number;
    gc(): void;
    print(expression: string): void;
    qsTr(sourceText: string, disambiguation: string, n: number): string;
    qsTranslate(context: string, sourceText: string, disambiguation: string): string;
    qsTrId(id: string, n: number): string;
    QT_TR_NOOP(sourceText: string): string;
    QT_TRANSLATE_NOOP(context: string, sourceText: string): string;
    acceptUndo(caption: string): void;
    backgroundProgressIsActive(): boolean;
    backgroundProgressIsCancelled(): boolean;
    beginNodeSelectionHold(): void;
    beginUndo(): void;
    beginViewportRedrawLock(): void;
    cancelBackgroundProgress(): void;
    cancelProgress(): void;
    cancelUndo(): void;
    clearBusyCursor(): void;
    clearNodeSelectionHolds(): void;
    clearUndoStack(): void;
    clearViewportRedrawLocks(): void;
    connect(sender: any, signal: string, receiver: any, _function: string): void;
    connect(sender: any, signal: string, thisObject: any, functionRef: Function): void;
    connect(sender: any, signal: string, functionRef: Function): void;
    debug(arg0: expression): void;
    disconnect(sender: any, signal: string, functionRef: Function): void;
    disconnect(sender: any, signal: string, thisObject: any, functionRef: Function): void;
    disconnect(sender: any, signal: string, receiver: any, _function: string): void;
    dropNodeSelectionHold(): void;
    dropUndo(): void;
    dropViewportRedrawLock(): void;
    finishBackgroundProgress(): void;
    finishBackgroundProgressWithDetail(): any;
    finishProgress(): void;
    finishProgressWithDetail(): any;
    getArguments(): any[];
    getErrorMessage(errCode: DzError): string;
    getObjectParent(obj: QObject): QObject;
    getScriptAuthor(): DzAuthor;
    getScriptFileName(): string;
    getScriptType(): string;
    getScriptVersionString(): string;
    pointersAreEqual(ptr1: QObject, ptr2: QObject): boolean;
    processEvents(): void;
    progressIsActive(): boolean;
    progressIsCancelled(): boolean;
    restoreNodeSelectionHold(): void;
    setBackgroundProgressInfo(info: string): void;
    setBusyCursor(): void;
    setProgressInfo(info: string): void;
    sleep(milliseconds: number): void;
    startBackgroundProgress(info: string, totalSteps: number, isCancellable: boolean): void;
    startProgress(info: string, totalSteps: number, isCancellable: boolean, showTimeElapsed: boolean): void;
    stepBackgroundProgress(numSteps: number): void;
    stepProgress(numSteps: number): void;
    updateBackgroundProgress(position: number): void;
    updateProgress(position: number): void;
    unescape(text: string): string;
    escape(text: string): string;
    shiftPressed(): boolean;
    ctrlPressed(): boolean;
    getDesktop(): QDesktopWidget;
    include(scriptPath: string): void;
}

/**
 * No description available.
 */
declare class DzGraftingFigureShape {
    getOrignalToWeldMeshList(): any[];
    getOrignalToWeldMeshMapSize(): number;
    getWeldMeshToOrginalList(): any[];
    getWeldMeshToOrginalMapSize(): number;
    hasWeldedFollowers(): boolean;
    updateBuilder(): void;
}

/**
 * A layout that manages child items in a grid of columns/rows.
 */
declare class DzGridLayout {
    addLayout(item: DzLayout, row: number, col: number, rowSpan: number, colSpan: number): void;
    addWidget(item: DzWidget, row: number, col: number, rowSpan: number, colSpan: number): void;
    colCount(): number;
    colSpacing(col: number): number;
    colStretch(col: number): number;
    rowCount(): number;
    rowSpacing(row: number): number;
    rowStretch(row: number): number;
    setColSpacing(col: number, minSize: number): void;
    setColStretch(col: number, stretch: number): void;
    setRowSpacing(row: number, minSize: number): void;
    setRowStretch(row: number, stretch: number): void;
    addMultiCellWidget(item: DzWidget, fromRow: number, toRow: number, fromCol: number, toCol: number): void;
    addMultiCellLayout(item: DzLayout, fromRow: number, toRow: number, fromCol: number, toCol: number): void;
}

/**
 * Provides a group box frame, with an optional title and an ability to be checked like a DzCheckBox .
 */
declare class DzGroupBox {
    alignment(): AlignmentFlags;
    checkable: boolean;
    checked: boolean;
    columns: number;
    flat: boolean;
    insideMargin: number;
    insideSpacing: number;
    orientation: Orientation;
    title: string;

    addSpace(space: number): void;

    // SIGNALS
    clicked(checked: boolean): void;
    toggled(onOff: boolean): void;
}

/**
 * This specialized DzNode is intended for grouping multiple nodes in the scene under one parent node. This allows easy transformation, visibility and/or selectability of the whole group. The bounding box of the group is calculated by getting the world space bounding box of the immediate children of the group node. This allows better use of framing the group to see the whole of the contents of the group.
 */
declare class DzGroupNode {
}

/**
 * Guide Pages are intended as a dynamic means of providing users with instructions on how to use a portion of the User Interface ( UI ), and/or provide widgets that simplify the process of getting started where an otherwise non-descript area of the UI would be displayed. These pages are typically found within a DzPane via instances of filecontenttab_dz or productcontenttab_dz , or within an embedded instance of productassetsview_dz or associatedassetsview_dz .
 */
declare class DzGuidePage {
    defaultScriptPath(): string;
    isCurrentPage(): boolean;
    makeCurrentPage(onOff: boolean): void;
    reload(): DzError;
    scriptFilename(): string;
    setUiScript(scriptPath: string): DzError;
}

/**
 * This class provides DAZ Script functionality for reading and writing *.gz ('gzipped') files. A high-level interface for zipping/unzipping files is provided with the functions zip () and unzip (). Also, a low-level interface is provided, allowing scripts to read and write compressed files directly.
 */
declare class DzGZFile {
    close(): void;
    eof(): boolean;
    open(accessMode: AccessMode): boolean;
    read(): string;
    readByte(): number;
    readByteLine(): ByteArray;
    readLine(): string;
    readLines(): any[];
    unzip(filename: string): boolean;
    write(data: string, length: number): void;
    writeByte(byte: number): void;
    writeLine(data: string): void;
    zip(filename: string): boolean;
}

/**
 * Provided as a convenience for creating a DzBoxLayout where the direction is automatically initially set to DzBoxLayout :: LeftToRight .
 */
declare class DzHBoxLayout {
}

/**
 * Provides a DzButtonGroup with a horizontal layout. Deprecated Exists only to keep old code working. Do not use in new code. Use DzButtonGroup for state management and DzGroupBox in conjunction with DzHBoxLayout for visual representation instead.
 */
declare class DzHButtonGroup {
}

/**
 * See Also: DzListView :: header ()
 */
declare class DzHeader {
    clickEnabled(): boolean;
    movingEnabled: boolean;
    resizeEnabled: boolean;
    stretchEnabled: boolean;

    isClickEnabled(section: number): bool;
    isResizeEnabled(section: number): bool;
    isStretchEnabled(section: number): boolean;
    setClickEnabled(enable: boolean, section: number): void;
    setResizeEnabled(enable: boolean, section: number): void;
    setStretchEnabled(enable: boolean, section: number): void;

    // SIGNALS
    clicked(section: number): void;
    indexChange(section: number, fromIndex: number, toIndex: number): void;
    pressed(section: number): void;
    released(section: number): void;
    sectionHandleDoubleClicked(section: number): void;
    sizeChange(section: number, oldSize: number, newSize: number): void;
}

/**
 * This class manages help documentation for the application. There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getHelpMgr (). See Also: Global :: App
 */
declare class DzHelpMgr {
    browseToIdentifier(identifier: string): void;
    browseToKeyword(keyword: string): void;
    browseToPage(page: string): void;
    browseToUrl(url: string): void;
    findFilterAttributes(name: string): any[];
    findIdentifierUrl(id: string): string;
    findKeywordUrl(keyword: string): string;
    getDescription(label: string): string;
    getFilterAttributes(which: number): any[];
    getFilterName(which: number): string;
    getGroup(label: string): string;
    getGroups(): any[];
    getHelpItemLabels(): any[];
    getHelpString(label: string): string;
    getHelpStringReplacement(group: string, key: string): string;
    getHelpStringReplacementGroups(): any[];
    getHelpStringReplacementKeys(group: string): any[];
    getIdentifier(which: number): string;
    getIdentifierUrl(which: number): string;
    getKeyword(which: number): string;
    getKeywordUrl(which: number): string;
    getNumFilters(): number;
    getNumIdentifiers(): number;
    getNumKeywords(): number;
    getStatusTip(label: string): string;
    getToolTip(label: string): string;
    hasHelpItem(label: string): boolean;
    isHelpItemUsed(label: string): boolean;
    removeHelpItem(label: string): boolean;
    renameHelpItem(oldLabel: string, newLabel: string): boolean;
    saveHelpItems(filename: string, groups: any[], labels: any[]): DzError;
    setDescription(label: string, description: string): void;
    setGroup(label: string, group: string): void;
    setHelpItem(label: string, group: string, description: string, toolTip: string, statusTip: string, helpString: string): void;
    setHelpString(label: string, helpString: string): void;
    setHelpStringReplacement(group: string, key: string, value: string): void;
    setStatusTip(label: string, statusTip: string): void;
    setToolTip(label: string, toolTip: string): void;
    updateHelp(widget: QWidget): void;
    updateHelp(action: DzAction): void;
}

/**
 * Provides a DzGroupBox with a horizontal layout.
 */
declare class DzHGroupBox {
}

/**
 * An asset save filter for saving a Hierarchical Material(s) Preset in the DSON format. See Also: Sample: Save a Hierarchical Material(s) Preset
 */
declare class DzHierarchicalMaterialAssetFilter {
}

/**
 * An asset save filter for saving a Hierarchical Pose Preset in the DSON format. See Also: Sample: Save a Hierarchical Pose Preset
 */
declare class DzHierarchicalPoseAssetFilter {
}

/**
 * Provides a simple implementation of the HTTP protocol. See Also: Sample: Get Store Product Data
 */
declare class DzHttpHelper {
    abort(): void;
    doAsynchronousRequest(content: ByteArray): void;
    doSynchronousRequest(content: ByteArray): ByteArray;
    getError(): string;
    setConnectionMode(mode: string): void;
    setContentType(type: string): void;
    setHeaderValues(keys: any[], values: any[]): void;
    setHost(host: string): void;
    setPath(path: string): void;
    setQueryString(query: string): void;
    setRequestMethod(method: string): void;

    // SIGNALS
    received(bytes: ByteArray): void;
}

/**
 * This is the script counterpart to the QImage type used in the C++ SDK. Attention: Inheritance will change to Object in a pending update.
 */
declare class Image {
    alphaBuffer(): boolean;
    depth: number;
    dotsPerMeterX: number;
    dotsPerMeterY: number;
    format: Format;
    height: number;
    numColors: number;
    offset: Point;
    size: Size;
    width: number;

    color(index: number): { r: number, g: number, b: number, a: number };
    compositeAtop(other: Image, x: int, y: int): Image;
    compositeColorBurn(other: Image, x: int, y: int): Image;
    compositeColorDodge(other: Image, x: int, y: int): Image;
    compositeDarken(other: Image, x: int, y: int): Image;
    compositeDifference(other: Image, x: int, y: int): Image;
    compositeExclusion(other: Image, x: int, y: int): Image;
    compositeHardLight(other: Image, x: int, y: int): Image;
    compositeIn(other: Image, x: int, y: int): Image;
    compositeLighten(other: Image, x: int, y: int): Image;
    compositeMultiply(other: Image, x: int, y: int): Image;
    compositeOut(other: Image, x: int, y: int): Image;
    compositeOver(other: Image, x: number, y: number): Image;
    compositeOverlay(other: Image, x: int, y: int): Image;
    compositePlus(other: Image, x: int, y: int): Image;
    compositeScreen(other: Image, x: int, y: int): Image;
    compositeSoftLight(other: Image, x: int, y: int): Image;
    compositeXor(other: Image, x: int, y: int): Image;
    convertDepth(depth: number): Image;
    copy(x: number, y: number, w: number, h: number): Image;
    copy(rect: Rect): Image;
    copy(): Image;
    create(w: number, h: number, depth: number, numColors: number): void;
    create(size: Size, depth: number, numColors: number): void;
    drawText(x: number, y: number, text: string, font: Font, color: { r: number, g: number, b: number, a: number }, flags: number): Rect;
    fill(color: { r: number, g: number, b: number, a: number }): void;
    getColorMask(maskColor: { r: number, g: number, b: number, a: number }, invert: boolean, tolerance: number): Image;
    invertPixels(invertAlpha: boolean): void;
    isNull(): boolean;
    load(filename: string, format: string): boolean;
    loadFromData(data: ByteArray, format: string): boolean;
    mirror(): Image;
    mirror(horizontal: bool, vertical: bool): Image;
    pixel(x: number, y: number): { r: number, g: number, b: number, a: number };
    save(filename: string): void;
    scale(size: Size): Image;
    scale(width: number, height: number): Image;
    setAlphaFromImage(img: Image): boolean;
    setColor(index: number, color: { r: number, g: number, b: number, a: number }): void;
    setPixel(x: number, y: number, color: { r: number, g: number, b: number, a: number }): void;
    setText(key: string, text: string): void;
    smoothScale(width: number, height: number): Image;
    smoothScale(size: Size): Image;
    swapRGB(): Image;
    text(key: string): void;
    textKeys(): any[];
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureLayer instead.
 */
declare class DzImageBlend {
    blendImage(dest: Image, src: Image): void;
    getDescription(): string;

    // SIGNALS
    blendMethodChanged(): void;
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureLayer instead.
 */
declare class DzImageColorLayer {
    color(): { r: number, g: number, b: number, a: number };

    setSize(size: Size): void;

    // SIGNALS
    colorChanged(color: { r: number, g: number, b: number, a: number }): void;
    sizeChanged(size: Size): void;
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureComponent instead.
 */
declare class DzImageComponent {
    label(): string;
    visible: boolean;

    addManipulator(deprecated: DzImageManip): void;
    freeImageData(): void;
    getImageData(): Image;
    getManipulator(idx: number): DzImageManip;
    getNumManipulators(): number;
    getSize(): Size;
    insertManipulator(idx: number, deprecated: DzImageManip): void;
    removeManipulator(idx: number): boolean;
    removeManipulator(deprecated: DzImageManip): boolean;
    toTextureLayer(layer: DzTextureLayer, imageSize: Size): boolean;

    // SIGNALS
    imageDataChanged(): void;
    labelChanged(label: string): void;
    manipulatorListChanged(): void;
    visibilityChanged(onOff: boolean): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzImageExporter {
    getDescription(): string;
    getExtension(): string;
    isFileExporter(): boolean;
    saveImage(filename: string, image: Image): DzError;
    saveImage(filename: string, image: Image, options: DzFileIOSettings): DzError;
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureLayer instead.
 */
declare class DzImageFileLayer {
    filename(): string;

    // SIGNALS
    filenameChanged(filename: string): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzImageImporter {
    getDescription(): string;
    getExtension(i: number): string;
    getNumExtensions(): number;
    loadImage(filename: string, image: Image, options: DzFileIOSettings): DzError;
    loadImage(filename: string, image: Image): DzError;
    recognize(filename: string): boolean;
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureLayer instead.
 */
declare class DzImageLayer {
    getBlendMode(): DzImageBlend;
    getDescription(): string;
    getMask(): DzImageMask;
    setBlendMode(deprecated: DzImageBlend): void;
    setMask(deprecated: DzImageMask): void;

    // SIGNALS
    blendModeChanged(deprecated: DzImageBlend): void;
    maskChanged(deprecated: DzImageMask): void;
}

/**
 * Image manipulators are applied to an image layer before it is blended into the final image. Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureComponent instead.
 */
declare class DzImageManip {
    getDescription(): string;
    manipulate(img: Image): void;

    // SIGNALS
    manipulationChanged(): void;
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureMask instead.
 */
declare class DzImageMask {
    filename(): string;

    // SIGNALS
    filenameChanged(filename: string): void;
}

/**
 * Responsible for the management of image (texture) importers/exporters, as well as the lifetime (loading/unloading) and preparation (for display/rendering) of images used as textures for scene items. There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getImageMgr (). See Also: Global :: App DzImageImporter DzImageExporter DzTexture DzLayeredTexture DzLayeredImage (deprecated)
 */
declare class DzImageMgr {
    getExporterInfo(i: number): any;
    getImageSize(imagePath: string): Size;
    getImporterInfo(i: number): any;
    getNumExporters(): number;
    getNumImporters(): number;
    beginEditingImage(): void;
    createLayeredTexture(name: string): DzLayeredTexture;
    deleteUnusedTextureObjects(): void;
    findImage(fullPath: string): DzTexture;
    findImageByName(name: string): DzTexture;
    findLayeredTexture(uri: DzUri): DzLayeredTexture;
    findTexture(uri: DzUri): DzTexture;
    finishedEditingImage(img: DzTexture): void;
    getImage(which: number): DzTexture;
    getImage(fullPath: string, creationGamma: number): DzTexture;
    getImage(fullPath: string): DzTexture;
    getImage(fullPath: string, creationGamma: number, creationType: number): DzTexture;
    getImageOpenPath(): string;
    getImageSavePath(): string;
    getNumImages(): number;
    getUniqueImageName(name: string): string;
    imagePrepared(img: DzTexture, tempName: string): void;
    loadImage(filename: string): Image;
    loadImage(filename: string, img: Image, importerIdx: number): DzError;
    prepareAllImages(r: DzRenderer): void;
    refresh(): void;
    saveImage(filename: string, image: Image, exporterIdx: number): DzError;
    setImageOpenPath(path: string): void;
    setImageSavePath(path: string): void;

    // SIGNALS
    autoRefreshChanged(onOff: boolean): void;
    imageListChanged(): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzImageProperty {
    getDefaultMapGamma(): number;
    getDefaultMapTextureType(): number;
    getTextureModifier(): DzTextureModifier;
    getTextureModifierFlags(): number;
    getValue(): DzTexture;
    setDefaultMapGamma(gamma: number): void;
    setDefaultMapTextureType(type: number): void;
    setTextureModifier(txtMod: DzTextureModifier): void;
    setTextureModifierFlags(flags: number): void;
    setValue(val: DzTexture): boolean;
    setValue(imgFile: string): boolean;

    // SIGNALS
    defaultMapGammaChanged(): void;
    defaultMapTextureTypeChanged(): void;
    textureModifierChanged(): void;
    textureModifierFlagsChanged(): void;
}

/**
 * Has an array of QImage objects for capturing data from a renderer - one image will be created for each frame rendered.
 */
declare class DzImageRenderHandler {
    postProcessOnRenderFinish(): boolean;
    writeToFile: boolean;

    addRenderFiles(files: any[]): void;
    beginFrame(frame: number): void;
    beginRender(): void;
    finishFrame(): void;
    finishRender(): void;
    getCreateThumbnail(): boolean;
    getCurrentFrameImage(): Image;
    getFilename(): string;
    getNumFrames(): number;
    getSize(): Size;
    getStartingTime(): number;
    setCreateThumbnail(createThumb: boolean): void;
}

/**
 * This class is not intended to be constructed directly. Create (or retrieve) an instance from DzImageMgr - this ensures that there is only one instance of a given image in memory at a time, and also ensures that necessary conversions for rendering the image occurs correctly. See Also: DzImageMgr :: findImage () DzImageMgr :: findImageByName () DzImageMgr :: findTexture () DzImageMgr :: getImage ()
 */
declare class DzImageTexture {
    assetAuthor(): DzAuthor;
    assetFileRevision: DzVersion;
    assetId: string;
    assetModifiedDate: Date;
    assetNeedSave: boolean;
    assetSource: DzUri;
    assetUri: DzUri;

    // SIGNALS
    assetModified(): void;
    assetWasSaved(): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzImporter {
    getDescription(): string;
    getExtension(i: number): string;
    getImportedNode(i: number): DzNode;
    getNumExtensions(): number;
    getNumImportedNodes(): number;
    readFile(filename: string, options: DzFileIOSettings): DzError;
    readFile(filename: string): DzError;
    recognize(filename: string): boolean;
}

/**
 * There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getImportMgr (). See Also: Global :: App Samples: Importers
 */
declare class DzImportMgr {
    canImport(filename: string): boolean;
    findImporter(filename: string): DzImporter;
    findImporterByClassName(className: string): DzImporter;
    findImporterIndex(filename: string): number;
    getNumImporters(): number;
    makeGeometryFileFilter(filter: DzFileFilter, defaultFilter: string, makeAllFilesEntry: boolean): void;
    makeImportFileFilter(filter: DzFileFilter, defaultFilter: string, makeAllFilesEntry: boolean): void;
    getImportFileName(): string;
    getImportPath(): string;
    isImporting(): boolean;
    readFile(filename: string, importerIdx: number): DzError;
    readFile(filename: string, importerIdx: number, options: DzFileIOSettings): DzError;
    readGeometry(filename: string, importerIdx: number, options: DzFileIOSettings): DzShape;
    readGeometry(filename: string, importerIdx: number): DzShape;
    setImportFileName(fileName: string): void;
    setImportPath(path: string): void;

    // SIGNALS
    fileImported(): void;
    fileImportStarting(): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzIndexList {
    addIndex(idx: number): void;
    addIndices(list: DzIndexList): void;
    addSortedIndex(idx: number): void;
    clear(): void;
    count(): number;
    findIndex(idx: number): number;
    getIndex(i: number): number;
    getMaxIndex(): number;
    insertIndex(idx: number): number;
    insertSortedIndex(idx: number): number;
    preSizeArray(count: number): void;
    removeComponent(idx: number): boolean;
    removeIndex(idx: number): boolean;
    removeIndexes(toRemove: DzIndexList): boolean;
    toList(): any[];
    toString(): string;
    toVector(): any[];
}

/**
 * DzInfoDivider places a divider bar between your widget and a tab bar of info tabs. This class is very similar (but not exactly like) DzDynamicDividerWgt . For situations where you want to control both sides of the divider bar it is recommended to use DzDynamicDividerWgt .
 */
declare class DzInfoDivider {
    getActualDividerPercent(): number;
    getInfoTabs(): DzInfoTabs;
    getPreferredDividerPercent(): number;
    getToggleState(): number;
    isMinimized(): boolean;
    isToggled(): boolean;
    moveDivider(distance: number): void;
    setPreferredDividerPercent(distance: number): void;
    setToggleState(state: number): void;
    toggleClosed(): void;
    toggleEnabled(): boolean;
    toggleMinimized(): void;
}

/**
 * Tab bar that provides Tips, MetaData, and Info tabs that can be used to provide various information about products.
 */
declare class DzInfoTabs {
    currentTab(): number;
    getTipDefaultScriptPath(): string;
    getTipScriptPath(): string;
    hideStack(): void;
    isStackHidden(): boolean;
    reloadTip(): DzError;
    setCurrentTab(which: number): void;
    setFileInfo(asset: DzAsset): void;
    setInfo(asset: DzAsset): void;
    setMetaInfo(asset: DzAsset): void;
    setNodeInfo(node: DzNode): void;
    setProductInfo(product: DzProductAssetContainer): void;
    setTipUIScript(path: string): DzError;
    showFileTab(onOff: boolean): void;
    showMetaTab(onOff: boolean): void;
    showNodeTab(onOff: boolean): void;
    showRenderTab(onOff: boolean): void;
    showStack(): void;
    showStoreTab(onOff: boolean): void;

    // SIGNALS
    keywordAddUniqueClicked(keyword: string): void;
    keywordSetClicked(keyword: string): void;
    renderApplyClicked(): void;
}

/**
 * An instance group item is used to create a single lightweight clone of a DzNode (subclass) in the scene that has a DzObject , within a group of like clones - a group of clones of the same node. This lightweight clone is drawn the same as the node that it is a clone of with the exception of transforms. See Also: DzNode :: getObject () DzInstanceGroupNode DzInstanceNode
 */
declare class DzInstanceGroupItem {
    copyTransformFromNode(node: DzNode): void;
    copyTransformToNode(node: DzNode): void;
    getEndPointValues(): DzVec3;
    getGeneralScaleValue(): number;
    getLabel(): string;
    getLocalPos(): DzVec3;
    getLocalRot(): DzQuat;
    getLocalScale(): DzMatrix3;
    getLocalTransform(): DzMatrix3;
    getOrientation(): DzQuat;
    getOrientationValues(): DzVec3;
    getOriginValues(): DzVec3;
    getPositionValues(): DzVec3;
    getRotationOrder(): DzRotationOrder;
    getRotationValues(): DzVec3;
    getWSPos(tm: number, defaultVal: boolean): DzVec3;
    getWSPos(): DzVec3;
    getWSRot(tm: number, defaultVal: boolean): DzQuat;
    getWSRot(): DzQuat;
    getWSScale(tm: number, defaultVal: boolean): DzMatrix3;
    getWSScale(): DzMatrix3;
    getWSTransform(): DzMatrix3;
    getWSTransform(tm: number, defaultVal: boolean): DzMatrix3;
    getXYZScaleValues(): DzVec3;
    inheritsScale(): boolean;
    setEndPoint(x: number, y: number, z: number): void;
    setInheritScale(onOff: boolean): void;
    setLabel(label: string): void;
    setOrientation(x: number, y: number, z: number): void;
    setOrigin(x: number, y: number, z: number): void;
    setPosition(x: number, y: number, z: number): void;
    setRotation(x: number, y: number, z: number): void;
    setRotationOrder(order: DzRotationOrder): void;
    setScale(x: number, y: number, z: number, genScale: number): void;

    // SIGNALS
    localTransformChanged(): void;
    transformChanged(): void;
}

/**
 * An instance group node is used to group multiple lightweight clones of the same DzNode (subclass) in the scene that has a DzObject . These lightweight clones are drawn the same as the node that they are a clone of with the exception of their individual transforms. See Also: DzNode :: getObject () DzInstanceNode DzInstanceGroupItem
 */
declare class DzInstanceGroupNode {
    beginItemEdit(): void;
    clearItems(): void;
    createItem(): DzInstanceGroupItem;
    findIndexForItem(item: DzInstanceGroupItem): number;
    finishItemEdit(): void;
    getGroupItem(index: number): DzInstanceGroupItem;
    getNumberOfGroupItems(): number;
    isEditingItems(): boolean;
    removeItem(index: number): void;
}

/**
 * An instance node is used to create a single lightweight clone of a DzNode (subclass) in the scene that has a DzObject . This lightweight clone is drawn the same as the node that it is a clone of with the exception of transforms. See Also: DzNode :: getObject () DzInstanceGroupNode DzGeometryShellNode
 */
declare class DzInstanceNode {
    getCopyModeControl(): DzEnumProperty;
    getTarget(): DzNode;
    getTargetControl(): DzNodeProperty;

    // SIGNALS
    targetChanged(): void;
}

/**
 * See Also: DzVec2 Since: 4.6.4.88
 */
declare class DzInt2 {
    height(): number;
    width: number;
    x: number;
    y: number;

    abs(): void;
    add(vec: DzInt2): DzInt2;
    average(): number;
    clamp(min: number, max: number): void;
    clamped(min: number, max: number): DzInt2;
    clampedMax(max: number): DzInt2;
    clampedMin(min: number): DzInt2;
    clampMax(max: number): void;
    clampMin(min: number): void;
    divide(vec: DzInt2): DzInt2;
    identity(): DzInt2;
    isNull(): boolean;
    length(): number;
    lengthSquared(): number;
    linearInterp(t: number, v1: DzInt2, v2: DzInt2): DzInt2;
    makeIdentity(): void;
    makeZero(): void;
    manhattanLength(): number;
    modulate(min: number, max: number): DzInt2;
    modulo(min: number, max: number): void;
    multiply(vec: DzInt2): DzInt2;
    negate(): void;
    setLength(length: number): void;
    square(): void;
    subtract(vec: DzInt2): DzInt2;
    toString(): string;
    transpose(): void;
    zero(): DzInt2;
}

/**
 * This class provides an animatable integer property with 2 values that is stored and can be accessed as a DzInt2 . Since: 4.6.4.88
 */
declare class DzInt2Property {
    adjustInt2Value(val: DzInt2): DzInt2;
    adjustInt2Value(tm: number, val: DzInt2): DzInt2;
    getDefaultInt2Value(): DzInt2;
    getInt2FollowValue(): DzInt2;
    getInt2FollowValue(tm: number): DzInt2;
    getInt2Value(): DzInt2;
    getInt2Value(tm: number): DzInt2;
    getKeyInt2Value(i: number): DzInt2;
    getLocalInt2Value(): DzInt2;
    getLocalInt2Value(tm: number): DzInt2;
    getRawInt2Value(tm: number): DzInt2;
    getRawInt2Value(): DzInt2;
    setDefaultInt2Value(val: DzInt2): void;
    setInt2Value(val: DzInt2): void;
    setInt2Value(tm: number, val: DzInt2): void;
    setKeyInt2Value(i: number, val: DzInt2): void;
    setRawInt2Value(val: DzInt2): void;
    setRawInt2Value(tm: number, val: DzInt2): void;
}

/**
 * Since: 4.6.4.24
 */
declare class DzInteractiveInstructionObject {
    getMember(name: string): any;
    hasMember(name: string): boolean;
    removeMember(name: string): void;
    setMember(name: string, value: any): void;
}

/**
 * This class manages interactive lessons that the user can perform in the interface via lessonstripwgt_dz . There is only one instance of this manager in an application. This instance is created and owned by DzMainWindow . Request the instance via DzMainWindow :: getInteractiveLessonMgr (). See Also: Global :: MainWindow
 */
declare class DzInteractiveLessonMgr {
    progressWidth(): number;

    begin(path: string): void;
    begin(instructions: any[]): void;
    currentIndex(): number;
    currentPath(): string;
    currentQuery(): boolean;
    currentQuery(): number;
    currentQuery(): string;
    currentType(): string;
    getActionInstruction(classname: string, info: string, tag: string, locateOnly: boolean): string;
    getActivityInstruction(activity: string, info: string, tag: string, locateOnly: boolean): string;
    getDisplayInstruction(info: string, button: string): string;
    getInstruction(type: string, query: ByteArray, info: string, tag: string, locateOnly: boolean): string;
    getInstruction(type: string, query: string, info: string, tag: string, locateOnly: boolean): string;
    getInstruction(type: string, query: boolean, info: string, tag: string, locateOnly: boolean): string;
    getInstruction(type: string, query: number, info: string, tag: string, locateOnly: boolean): string;
    getLayoutInstruction(layout: string, info: string, tag: string, locateOnly: boolean): string;
    getWidgetInstruction(widgetPath: string, info: string, tag: string, locateOnly: boolean): string;
    instructionTypes(): any[];
    isRunning(): boolean;
    iterate(): void;
    skip(): void;
    stop(): void;

    // SIGNALS
    skipped(): void;
    started(): void;
    stepped(): void;
    stopped(success: boolean): void;
}

/**
 * Since: 4.6.4.24
 */
declare class DzInteractiveLessonObject {
    appendInstruction(): DzInteractiveInstructionObject;
    count(): number;
    currentIndex(): number;
    insertInstruction(index: number): DzInteractiveInstructionObject;
    instructionAt(index: number): DzInteractiveInstructionObject;
    nextInstruction(): DzInteractiveInstructionObject;
}

/**
 * TODO: Add detailed description.
 */
declare class DzIntProperty {
    adjustValue(val: number): number;
    adjustValue(tm: number, val: number): number;
    getDefaultValue(): number;
    getKeyValue(i: number): number;
    getLocalValue(tm: number): number;
    getLocalValue(): number;
    getMax(): number;
    getMin(): number;
    getRawValue(): number;
    getRawValue(tm: number): number;
    getSensitivity(): number;
    getValue(tm: number): number;
    getValue(): number;
    setDefaultValue(val: number): void;
    setKeyValue(i: number, val: number): void;
    setMax(max: number): void;
    setMin(min: number): void;
    setMinMax(min: number, max: number): void;
    setSensitivity(sens: number): void;
    setValue(tm: number, val: number): void;
    setValue(val: number): void;
}

/**
 * Provides a control that allows a user to adjust a bounded integer value.
 */
declare class DzIntSlider {
    defaultValue(): number;
    displayAsPercent: boolean;
    indeterminate: boolean;
    max: number;
    min: number;
    sensitivity: number;
    value: number;

    // SIGNALS
    editCancelled(): void;
    valueChanged(value: number): void;
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureComponent instead.
 */
declare class DzInvertManip {
    on(): boolean;

    isOn(): boolean;
    setOn(onOff: boolean): void;
}

/**
 * Implements a Physically Based Rendering (PBR) interface for the scene to render itself through the NVIDIA Iray renderer.
 */
declare class DzIrayRenderer {
    getAllowCPUFallback(): boolean;
    getAllowGPUDetection(): boolean;
    getCPULoadLimit(): number;
    getCPUThreadAffinityEnabled(): boolean;
    getGPUDriverCheck(): boolean;
    getGPULoadLimit(): number;
    getHighThreshold(): number;
    getMediumThreshold(): number;
    getNVLINKPeerGroupSize(): number;
    getPropertyHolder(): DzElement;
    isIPRRendering(): boolean;
    setAllowCPUFallback(onOff: boolean): void;
    setAllowGPUDetection(onOff: boolean): void;
    setCPULoadLimit(limit: number): boolean;
    setCPUThreadAffinityEnabled(onOff: boolean): boolean;
    setGPUDriverCheck(onOff: boolean): void;
    setGPULoadLimit(limit: number): boolean;
    setHighThreshold(val: number): void;
    setMediumThreshold(val: number): void;
    setNVLINKPeerGroupSize(size: number): void;
}

/**
 * This object implements ECMAScript JSON functions. One instance of the object is automatically created in the global namespace when the script engine is initialized. That instance is accessible via Global::JSON. Additional instances of the object cannot be created. See the ECMA script specification for more information.
 */
declare class JSON {
    parse(text: string, reviver: Function): any;
    stringify(value: any, replacer: any, space: any): string;
}

/**
 * Provides the ability to display text or an image to the user.
 */
declare class DzLabel {
    alignment(): AlignmentFlags;
    elideMode: TextElideMode;
    hasSelectedText: boolean;
    indent: number;
    openExternalLinks: boolean;
    pixmap: Pixmap;
    primitive: string;
    scaledContents: boolean;
    selectedText: string;
    text: string;
    textFormat: TextFormat;
    textInteractionFlags: TextInteractionFlags;
    textStyle: string;
    wordWrap: boolean;

    buddy(): DzWidget;
    clear(): void;
    setBuddy(buddy: DzWidget): void;

    // SIGNALS
    elideModeChanged(mode: TextElideMode): void;
    primitiveChanged(name: string): void;
    textFormatChanged(format: TextFormat): void;
    textInteractionFlagsChanged(flags: TextInteractionFlags): void;
    textStyleChanged(name: string): void;
}

/**
 * An asset save filter for saving a Layered Image(s) Preset in the DSON format. See Also: Sample: Save a Layered Image(s) Preset
 */
declare class DzLayerAssetFilter {
}

/**
 * Deprecated This class exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzLayeredTexture instead. This class uses explicit sharing to make it very efficient to copy. This does, however, mean that modifying one copy of the image modifies all copies. DzLayeredImage does not currently support detach() or copy() functions for creating unique instances or deep copies.
 */
declare class DzLayeredImage {
    addLayer(deprecated: DzImageLayer): void;
    getFlattenedImage(freeMem: boolean): Image;
    getLayer(which: number): DzImageLayer;
    getLayerCount(): number;
    getSize(): Size;
    insertLayer(deprecated: DzImageLayer, idx: number): void;
    moveLayer(from: number, to: number): void;
    removeLayer(deprecated: DzImageLayer): boolean;
    replaceLayer(deprecated: DzImageLayer, deprecated: DzImageLayer): boolean;
    setSize(size: Size): void;
    toLayeredTexture(img: DzLayeredTexture): boolean;

    // SIGNALS
    layerListChanged(): void;
    sizeChanged(size: Size): void;
}

/**
 * This class is not intended to be constructed directly. Create (or retrieve) an instance from DzImageMgr - this ensures that there is only one instance of a given layered texture in memory at a time, and also ensures that necessary conversions for rendering the layered texture occurs correctly. See Also: DzImageMgr :: createLayeredTexture () DzImageMgr :: findLayeredTexture ()
 */
declare class DzLayeredTexture {
    assetAuthor(): DzAuthor;
    assetFileRevision: DzVersion;
    assetId: string;
    assetModifiedDate: Date;
    assetNeedSave: boolean;
    assetSource: DzUri;
    assetUri: DzUri;
    size: Size;

    addLayer(layer: DzTextureLayer): void;
    beginEditing(): void;
    copyFrom(texture: DzLayeredTexture): void;
    createLayer(name: string): DzTextureLayer;
    endEditing(): void;
    findLayer(layer: DzTextureLayer): number;
    getLayer(index: number): DzTextureLayer;
    getNumLayers(): number;
    getSourceDSI(): string;
    insertLayer(index: number, layer: DzTextureLayer): void;
    moveLayer(fromIndex: number, toIndex: number): boolean;
    refeshLayeredTexture(): void;
    removeAllLayers(): void;
    removeLayer(index: number): boolean;
    removeLayer(layer: DzTextureLayer): boolean;
    replaceLayer(oldLayer: DzTextureLayer, newLayer: DzTextureLayer): boolean;
    takeLayer(index: number): DzTextureLayer;

    // SIGNALS
    aboutToInsertLayers(index: number, count: number): void;
    aboutToRemoveLayers(index: number, count: number): void;
    assetModified(): void;
    assetWasSaved(): void;
    layerListChanged(): void;
    layersInserted(index: number, count: number): void;
    layersRemoved(index: number, count: number): void;
    sizeChanged(size: Size): void;
}

/**
 * This is an abstract base class that provides general functionality for script interface layout components.
 */
declare class DzLayout {
    margin(): number;
    spacing: number;
    autoAdd: boolean;

    addWidget(item: DzWidget): void;
    getLayout(): QLayout;
}

/**
 * Provides a LCD-style number display. The following digits and symbols can be displayed: 0/O, 1, 2, 3, 4, 5/S, 6, 7, 8, 9/g, - (minus), . (decimal point), A, B, C, D, E, F, h, H, L, o, P, r, u, U, Y, : (colon), &deg; (degree sign - which is specified as single quote in the string) and space. Illegal characters are substituted with spaces.
 */
declare class DzLCDNumber {
    mode(): Mode;
    numDigits: number;
    segmentStyle: SegmentStyle;
    smallDecimalPoint: boolean;
    value: number;

    displayFloat(number: number): void;
    displayInt(number: number): void;
    displayString(number: string): void;
    display(number: string): void;
    display(number: number): void;

    // SIGNALS
    overflow(): void;
}

/**
 * This class is not intended to be constructed directly, rather it is created automatically by DzLegacyFigure . Create (or retrieve) an instance of DzLegacyFigure and create an “alternate geometry” via DzLegacyFigure :: addAlternateGeometry () or request one of its existing geometries via DzLegacyFigure :: getAlternateGeometry () or DzLegacyFigure :: findAlternateGeometry ().
 */
declare class DzLegacyAlternateGeometry {
    getBone(): DzBone;
    getFigure(): DzLegacyFigure;
    getObject(): DzObject;
}

/**
 * Provides access to and manages joints associated with a parametric mesh binding. This class is not intended to be constructed directly, rather it is created automatically by DzLegacyAlternateGeometry . Create (or retrieve) an instance of DzLegacyAlternateGeometry populated with a DzFacetMesh derived geometry and request its binding via findBinding ().
 */
declare class DzLegacyBinding {
    assetAuthor(): DzAuthor;
    assetFileRevision: DzVersion;
    assetId: string;
    assetModifiedDate: Date;
    assetNeedSave: boolean;
    assetSource: DzUri;
    assetUri: DzUri;
}

/**
 * A specialization of DzSkeleton that represents a figure where the associated geometry is bound to its bones using a set of parametrically defined joints. This type of figure is used to implement all figure content from the pre-Genesis era - i.e., all “legacy” format figure content. When loading legacy content, the application takes all geometry that would have previously been assigned to the individual bone instances for the figure and internally represents it as a “single skin” object owned by this class, in order to simplify/streamline the geometry pipeline. As such, the DzBone instances belonging to this figure no longer have a DzObject of their own. In addition to its base geometry, this type of figure supports defining a set of alternate geometries, which allows various aspects of the base geometry to be changed, or “swapped”, at runtime. Attention: As of version 4.0.1.34, DzMorph instances are only found on this node's DzObject , as opposed to the individual DzBone instances. All morph properties previously associated with the individual bones are now aliases to the morph properties rather than morph properties themselves. See Also: DzLegacyAlternateGeometry DzLegacyBinding
 */
declare class DzLegacyFigure {
    convertPropToFigure(srcNode: DzNode, rootBoneName: string, inheritSkeleton: boolean): DzLegacyFigure;
    addAlternateGeometry(bone: DzBone, createAlais: boolean): DzLegacyAlternateGeometry;
    addWeld(weld: DzWeld): void;
    boneUsedByWeld(bone: DzBone): boolean;
    clearVertexMaps(): void;
    findAlternateGeometry(bone: DzBone): DzLegacyAlternateGeometry;
    findAlternateGeometry(boneName: string): DzLegacyAlternateGeometry;
    findWeldByTargetBone(target: DzBone): DzWeld;
    findWeldByWeldBone(weldBone: DzBone): DzWeld;
    getAlternateGeometry(index: number): DzLegacyAlternateGeometry;
    getNumAlternateGeometries(): number;
    getNumWelds(): number;
    getWeld(which: number): DzWeld;
    invalidateVertexMaps(): void;
    removeAllWelds(): void;
    removeAlternateGeometry(alt: DzLegacyAlternateGeometry): bool;
    removeWeld(weld: DzWeld): void;

    // SIGNALS
    weldListChanged(): void;
}

/**
 * This is only intended to be used in conjunction with DzLegacyIKChains . It stores all the information from a single “inkyChain” section of a Poser CR2 file. See Also: DzLegacyIKChains
 */
declare class DzLegacyIKChain {
    addLink(node: DzNode, weight: number, index: number): void;
    clearLinks(): void;
    getActive(): boolean;
    getGoal(): DzNode;
    getLabel(): string;
    getLink(index: number): DzNode;
    getLinkWeight(index: number): number;
    getNumLinks(): number;
    removeLink(index: number): void;
    setActive(onOff: boolean): void;
    setGoal(node: DzNode): void;
    setLabel(label: string): void;
    setLinkWeight(index: number, weight: number): boolean;
}

/**
 * Implements a custom data item that allows a list of DzLegacyIKChain objects to be associated with a DzLegacyFigure of an imported Poser format figure. Each DzLegacyIKChain object in the list represents a single “inkyChain” section in the Poser CR2 file from which the figure was loaded. Can be used as follows to retrieve the IK chains from a Poser format figure that was loaded: See Also: DzElement :: addDataItem () DzElement :: removeDataItem () DzElement :: deleteDataItem () DzElement :: getNumDataItems () DzElement :: getDataItem () DzElement :: getDataItemList () DzElement :: findDataItem () DzElement :: moveDataItemToIndex () DzElement :: findDataItemIndex () DzLegacyIKChain
 */
declare class DzLegacyIKChains {
    addChain(chain: DzLegacyIKChain): void;
    getChain(index: number): DzLegacyIKChain;
    getNumChains(): number;
}

/**
 * TODO: Add detailed description.
 */
declare class DzLight {
    getCategories(): any[];
    getCategoriesControl(): DzStringProperty;
    getDiffuseColor(): { r: number, g: number, b: number, a: number };
    getShadowType(): ShadowType;
    getShadowTypeControl(): DzEnumProperty;
    getWSDirection(): DzVec3;
    isAreaLight(): boolean;
    isDirectional(): boolean;
    isOn(): boolean;

    // SIGNALS
    categoriesChanged(): void;
}

/**
 * An asset save filter for saving a Light(s) Preset in the DSON format. See Also: Sample: Save a Light(s) Preset
 */
declare class DzLightAssetFilter {
}

/**
 * TODO: Add detailed description.
 */
declare class DzLine3 {
    end(): DzVec3;
    origin: DzVec3;

    getDirection(): DzVec3;
    getPoint(t: number): DzVec3;
    length(t: number): number;
    linesIntersect(line: DzLine3, tolerance: number): any;
    minDistanceFromLine(line: DzLine3): any;
    minDistanceFromLineSquared(line: DzLine3): any;
    minDistanceFromPoint(pnt: DzVec3, clampEnds: boolean): any;
    minDistanceFromPointSquared(pnt: DzVec3, clampEnds: boolean): any;
    minDistanceFromRay(ray: DzLine3): any;
    minDistanceFromRaySquared(ray: DzLine3): any;
    negate(): void;
    planeIntersect(planePoint: DzVec3, planeNormal: DzVec3): any;
    segmentsIntersect(line: DzLine3, tolerance: number): any;
    setLength(length: number): void;
    swapEnds(): void;
    toString(): string;
}

/**
 * TODO: Add detailed description.
 */
declare class DzLinearPointLight {
    getFallOffEnd(): number;
    getFallOffEndControl(): DzFloatProperty;
    getFallOffStart(): number;
    getFallOffStartControl(): DzFloatProperty;
    setFallOffEnd(end: number): void;
    setFallOffStart(start: number): void;
}

/**
 * Provides a single line text editor to the user. See Also: DzComboEdit
 */
declare class DzLineEdit {
    acceptableInput(): boolean;
    alignment: AlignmentFlags;
    cursorPosition: number;
    echoMode: EchoMode;
    frame: boolean;
    hasSelectedText: boolean;
    inputMask: string;
    maxLength: number;
    modified: boolean;
    placeholderText: string;
    readOnly: boolean;
    redoAvailable: boolean;
    selectedText: string;
    text: string;
    undoAvailable: boolean;

    backspace(): void;
    clear(): void;
    clearModified(): void;
    copy(): void;
    cursorBackward(mark: boolean, steps: number): void;
    cursorForward(mark: boolean, steps: number): void;
    cursorWordBackward(mark: boolean, steps: number): void;
    cursorWordForward(mark: boolean, steps: number): void;
    cut(): void;
    del(): void;
    deselect(): void;
    end(mark: boolean): void;
    getValidatorSettings(): DzSettings;
    hasAcceptableInput(): boolean;
    hasSelectedText(): boolean;
    home(mark: boolean): void;
    paste(): void;
    redo(): void;
    selectAll(): void;
    selectedText(): string;
    selectionStart(): number;
    setDoubleValidator(bottom: number, top: number, decimals: number, scientific: boolean): void;
    setIntValidator(bottom: number, top: number): void;
    setRegExValidator(rx: string, caseSensitive: boolean): void;
    setSelection(start: number, length: number): void;
    setValidator(settings: DzSettings): void;
    undo(): void;

    // SIGNALS
    cursorPositionChanged(oldPos: number, newPos: number): void;
    editingFinished(): void;
    returnPressed(): void;
    selectionChanged(): void;
    textChanged(text: string): void;
    textEdited(text: string): void;
    lostFocus(): void;
}

/**
 * This modifier generates geometry along a polyline. The number of (user-definable) 'sides' represents the number of segments in a profile that is centered on, and perpendicular to, the starting segment of a polyline. This profile is then swept along the polyline to produce a 'ribbon' or 'tube' depending on the number of 'sides'. Attention: This modifier requires the shape for an object of a figure to be an instance of DzGraftingFigureShape to function as intended. See Also: DzFigure DzGraftingFigureShape Since: 4.11.0.70
 */
declare class DzLineTessellationModifier {
    getNumRenderSides(): number;
    getNumViewportSides(): number;
    getRenderSidesControl(): DzIntProperty;
    getViewportSidesControl(): DzIntProperty;
}

/**
 * TODO: Add detailed description.
 */
declare class DzListBox {
    columnMode(): LayoutMode;
    count: number;
    currentItem: number;
    currentText: string;
    numColumns: number;
    numItemsVisible: number;
    numRows: number;
    rowMode: LayoutMode;
    selected: number;
    selectionMode: SelectionMode;
    topItem: number;
    variableHeight: boolean;
    variableWidth: boolean;

    clear(): void;
    insertItem(text: string): void;
    isSelected(index: number): boolean;
    removeItem(index: number): void;
    setSelected(index: number, selected: boolean): void;
    text(index: number): string;

    // SIGNALS
    clicked(index: number): void;
    clicked(index: number, pnt: Point): void;
    contextMenuRequested(index: number, pos: Point): void;
    currentChanged(index: number): void;
    doubleClicked(index: number): void;
    highlighted(text: string): void;
    highlighted(index: number): void;
    mouseButtonClicked(button: number, index: number, pos: Point): void;
    mouseButtonPressed(button: number, index: number, pos: Point): void;
    onItem(index: number): void;
    onViewport(): void;
    pressed(index: number, pnt: Point): void;
    pressed(index: number): void;
    returnPressed(index: number): void;
    rightButtonClicked(index: number, pnt: Point): void;
    rightButtonPressed(index: number, pnt: Point): void;
    selected(index: number): void;
    selected(text: string): void;
    selectionChanged(): void;
    selectionChanged(index: number): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzListView {
    allColumnsShowFocus(): boolean;
    childCount: number;
    columns: number;
    defaultRenameAction: RenameAction;
    itemMargin: number;
    resizeMode: ResizeMode;
    rootIsDecorated: boolean;
    selectionMode: SelectionMode;
    showSortIndicator: boolean;
    showToolTips: boolean;
    sortColumn: number;
    sortOrder: SortOrder;
    treeStepSize: number;

    addColumn(label: string): number;
    clear(): void;
    clearSelection(): void;
    columnAlignment(column: number): number;
    columnText(column: number): string;
    columnWidth(column: number): number;
    columnWidthMode(column: number): WidthMode;
    currentItem(): DzListViewItem;
    deleteItem(item: DzListViewItem): void;
    ensureItemVisible(item: DzListViewItem): void;
    findItem(text: string, column: number, compare: number): DzListViewItem;
    firstChild(): DzListViewItem;
    getItems(mode: ItemsMode): any[];
    header(): DzHeader;
    hideColumn(column: number): void;
    isOpen(item: DzListViewItem): boolean;
    isRenaming(): boolean;
    isSelected(item: DzListViewItem): boolean;
    lastItem(): DzListViewItem;
    removeColumn(column: number): void;
    selectedItem(): DzListViewItem;
    setColumnAlignment(column: number, align: number): void;
    setColumnText(column: number, label: string): void;
    setColumnWidth(column: number, width: number): void;
    setColumnWidthMode(column: number, mode: WidthMode): void;
    setCurrentItem(item: DzListViewItem): void;
    setOpen(item: DzListViewItem, open: boolean): void;
    setSelected(item: DzListViewItem, selected: boolean): void;
    setSelectionAnchor(item: DzListViewItem): void;
    setSorting(column: number, ascending: boolean): void;
    sort(): void;

    // SIGNALS
    clicked(item: DzListViewItem): void;
    clicked(item: DzListViewItem, pos: Point, col: number): void;
    collapsed(item: DzListViewItem): void;
    contextMenuRequested(item: DzListViewItem, pos: Point, col: number): void;
    currentChanged(item: DzListViewItem): void;
    doubleClicked(item: DzListViewItem, pos: Point, col: number): void;
    expanded(item: DzListViewItem): void;
    itemRenamed(item: DzListViewItem, col: number, text: string): void;
    itemRenamed(item: DzListViewItem, col: number): void;
    mouseButtonClicked(button: number, item: DzListViewItem, pos: Point, col: number): void;
    mouseButtonPressed(button: number, item: DzListViewItem, pos: Point, col: number): void;
    pressed(item: DzListViewItem, pos: Point, col: number): void;
    pressed(item: DzListViewItem): void;
    returnPressed(item: DzListViewItem): void;
    rightButtonClicked(item: DzListViewItem, pos: Point, col: number): void;
    rightButtonPressed(item: DzListViewItem, pos: Point, col: number): void;
    selectionChanged(): void;
    selectionChanged(item: DzListViewItem): void;
    spacePressed(item: DzListViewItem): void;
}

/**
 * This is not a widget, but a helper for working with DzListView . Each DzListViewItem represents a single item in a list view - add items to a list view by creating a new DzListViewItem that is a child of the list view, or a child of another list view item in the list view.
 */
declare class DzListViewItem {
    dragEnabled(): boolean;
    dropEnabled: boolean;
    enabled: boolean;
    expandable: boolean;
    height: number;
    id: number;
    multiLinesEnabled: boolean;
    open: boolean;
    selectable: boolean;
    selected: boolean;
    visible: boolean;

    addDataItem(key: string, val: any): void;
    childCount(): number;
    compare(item: DzListViewItem, column: number, ascending: boolean): number;
    deleteItem(item: DzListViewItem): void;
    depth(): number;
    firstChild(): DzListViewItem;
    getDataItem(key: string): any;
    getNumDataItems(): number;
    insertItem(newChild: DzListViewItem): void;
    itemAbove(): DzListViewItem;
    itemBelow(): DzListViewItem;
    key(column: number, ascending: boolean): string;
    listView(): DzListView;
    moveItem(item: DzListViewItem): void;
    nextSibling(): DzListViewItem;
    parent(): DzListViewItem;
    removeItem(item: DzListViewItem): void;
    renameEnabled(column: number): boolean;
    setPixmap(column: number, pixmap: Pixmap): void;
    setRenameEnabled(column: number, yesNo: boolean): void;
    setText(column: number, text: string): void;
    sort(): void;
    sortChildItems(column: number, ascending: boolean): void;
    startRename(column: number): void;
    text(column: number): string;
}

/**
 * There is only one of these widgets in the application, which is created and owned by DzApp . It can be accessed by using the Global :: MainWindow variable.
 */
declare class DzMainWindow {
    alwaysOnTop(): boolean;
    toolTipsEnabled: boolean;

    askSaveChanges(): boolean;
    askTurnOffLimits(): boolean;
    checkExistingFile(filename: string): boolean;
    clearUIPopUp(): void;
    displayPrompt(msg: string, msecs: number): void;
    dockArea(pos: Point): DzDockArea;
    doFileExport(parent: QWidget): boolean;
    doFileImport(parent: QWidget): boolean;
    doFileMerge(parent: QWidget): boolean;
    doFileOpen(parent: QWidget): boolean;
    doFileSave(parent: QWidget): boolean;
    doFileSaveAs(parent: QWidget, startWith: string): boolean;
    doImageOpen(parent: QWidget): Image;
    doImageSaveAs(image: Image, parent: QWidget): boolean;
    doNewFile(): boolean;
    doVideoClipSaveAs(clip: DzVideoClip, parent: QWidget): boolean;
    exitFullScreen(): void;
    getActionMgr(): DzActionMgr;
    getBottomDockArea(): DzDockArea;
    getCenterDockArea(): DzDockArea;
    getInteractiveLessonMgr(): DzInteractiveLessonMgr;
    getLeftDockArea(): DzDockArea;
    getPaneMgr(): DzPaneMgr;
    getRightDockArea(): DzDockArea;
    getSliderMouseDragScalar(): number;
    getTopDockArea(): DzDockArea;
    getUIPopUp(): DzUIPopUpWgt;
    getViewportMgr(): DzViewportMgr;
    goFullScreen(): void;
    isUILocked(): boolean;
    positionUIPopUp(posWgt: QWidget): void;
    removePrompt(): void;
    repaintActive3DViewport(): void;
    restoreUILockState(): void;
    setSliderMouseDragScalar(val: number): void;
    setUILocked(onOff: boolean, storeSetting: boolean): void;
    showHomeDlg(): void;
    showUIPopUpWgt(filename: string, posWgt: QWidget): DzUIPopUpWgt;
    toggleUIPopUpWgt(filename: string, posWgt: QWidget): DzUIPopUpWgt;

    // SIGNALS
    aboutToClose(): void;
    alwaysOnTopChanged(onOff: boolean): void;
    sliderMouseDragScalarChanged(scalar: number): void;
    started(): void;
    uiLockedChanged(): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzMap {
    appendFloatValue(val: number): void;
    appendIntValue(val: number): void;
    appendPnt2Vec(val: DzVec3): void;
    appendPnt3Vec(val: DzVec3): void;
    appendShortValue(val: number): void;
    clearAllData(): void;
    getFloatMax(idx: number): number;
    getFloatMin(idx: number): number;
    getFloatValue(idx: number): number;
    getIntValue(idx: number): number;
    getIntValueMax(idx: number): number;
    getIntValueMin(idx: number): number;
    getLabel(): string;
    getNumDimensions(): number;
    getNumValues(): number;
    getOrderingGeometry(): DzGeometry;
    getPnt2Vec(idx: number): DzVec3;
    getPnt2VecMax(idx: number): DzVec3;
    getPnt2VecMin(idx: number): DzVec3;
    getPnt3Vec(idx: number): DzVec3;
    getPnt3VecMax(idx: number): DzVec3;
    getPnt3VecMin(idx: number): DzVec3;
    getShortValue(idx: number): number;
    getShortValueMax(idx: number): number;
    getShortValueMin(idx: number): number;
    getType(): MapType;
    inUnitSpace(): boolean;
    invalidateMinMax(): void;
    makeCopy(): DzMap;
    preSize(num: number): void;
    setDefaultFloatValue(defaultVal: number): void;
    setDefaultIntValue(defaultVal: number): void;
    setDefaultPnt2Vec(defaultVal: DzVec3): void;
    setDefaultPnt3Vec(defaultVal: DzVec3): void;
    setDefaultShortValue(defaultVal: number): void;
    setFloatValue(idx: number, val: number): void;
    setIntValue(idx: number, val: number): void;
    setLabel(label: string): void;
    setMapType(mapType: MapType, keepData: boolean): void;
    setNumValues(num: number): void;
    setPnt2Vec(idx: number, val: DzVec3): void;
    setPnt3Vec(idx: number, val: DzVec3): void;
    setShortValue(idx: number, val: number): void;

    // SIGNALS
    labelChanged(): void;
    mapModified(): void;
}

/**
 * A “material” represents a collection of properties and settings that, when applied through the use of a “shader” (a small program/subroutine that describes how the settings are used), describe how the geometry associated with a 3D object interacts with light and ultimately what the surface of that 3D object looks like when rendered. See Also: DzShape DzFacetMesh DzMaterialFaceGroup materialselectionset_dz
 */
declare class DzMaterial {
    assetAuthor(): DzAuthor;
    assetFileRevision: DzVersion;
    assetId: string;
    assetModifiedDate: Date;
    assetNeedSave: boolean;
    assetSource: DzUri;
    assetUri: DzUri;
    renderPriority: RenderPriority;

    getMaterial(which: number): DzMaterial;
    getNumMaterials(): number;
    duplicateOrDefaultMaterial(context: DzElementDuplicateContext): DzMaterial;
    enablePropagateRenderPriorityToNodes(propagate: boolean): void;
    getActiveUVSet(shape: DzShape): DzUVSet;
    getActiveUVSet(geom: DzGeometry): DzUVSet;
    getAllMaps(): any[];
    getBakedMap(): DzTexture;
    getBaseOpacity(): number;
    getBoundingBox(): DzBox3;
    getColorMap(): DzTexture;
    getDiffuseColor(): { r: number, g: number, b: number, a: number };
    getIndex(): number;
    getLineEndWidth(): float;
    getLineEndWidthControl(): DzFloatProperty;
    getLinePreviewColor(): { r: number, g: number, b: number, a: number };
    getLinePreviewColorControl(): DzColorProperty;
    getLineStartWidth(): float;
    getLineStartWidthControl(): DzFloatProperty;
    getLineUVWidth(): float;
    getLineUVWidthControl(): DzFloatProperty;
    getMaterialName(): string;
    getNumGLMaps(): number;
    getOpacityMap(): DzTexture;
    getPropagatePriorityControl(): DzBoolProperty;
    getRenderPriorityControl(): DzEnumProperty;
    getShaderLanguages(): any[];
    getShapeList(): any[];
    getSmoothAngleControl(): DzFloatProperty;
    getSmoothControl(): DzBoolProperty;
    getSmoothingAngle(): number;
    getTags(): any[];
    getTagsControl(): DzStringProperty;
    getUVSetControl(): DzEnumProperty;
    isColorMappable(): boolean;
    isHighlighted(): boolean;
    isOpacityMappable(): boolean;
    isOpaque(): boolean;
    isPropagateRenderPriorityToNodesEnabled(): boolean;
    isSelected(): boolean;
    isSmoothingOn(): boolean;
    modifyAsset(): boolean;
    modifyAsset(newUri: DzUri): boolean;
    needsPtex(): boolean;
    needsTangentSpaceParams(): boolean;
    select(onOff: boolean): void;
    setBakedMap(img: DzTexture): void;
    setBaseOpacity(val: number): void;
    setColorMap(img: DzTexture): void;
    setDiffuseColor(color: { r: number, g: number, b: number, a: number }): void;
    setLineEndWidth(width: number): void;
    setLinePreviewColor(color: { r: number, g: number, b: number, a: number }): void;
    setLineStartWidth(width: number): void;
    setLineUVWidth(width: number): void;
    setOpacityMap(img: DzTexture): void;
    setSmoothingAngle(angle: number): void;
    setSmoothingOn(onOff: boolean): void;
    shadersMatch(otherMat: DzMaterial): boolean;
    shouldAlwaysEmbed(): boolean;
    startDrawHighlight(): void;
    stopDrawHighlight(): void;
    getNumUVMaps(): number;

    // SIGNALS
    assetModified(): void;
    assetWasSaved(): void;
    bakedMapChanged(): void;
    lineUVWidthChanged(): void;
    lineWidthChanged(): void;
    selectionStateChanged(mat: DzMaterial, onOff: boolean): void;
    settingsChanged(): void;
    smoothingChanged(): void;
    tagsChanged(): void;
    uvsChanged(): void;
}

/**
 * An asset save filter for saving a Material(s) Preset in the DSON format. See Also: Sample: Save a Material(s) Preset
 */
declare class DzMaterialAssetFilter {
}

/**
 * Represents a list of material faces from a geometry that are collected into a group. The group is stored as a list of integers which are indices into the face list of the geometry which this group references. See Also: DzFacetMesh :: getNumMaterialGroups () DzFacetMesh :: getMaterialGroup () DzFacetMesh :: findMaterialGroup ()
 */
declare class DzMaterialFaceGroup {
}

/**
 * This object implements ECMAScript math functions. One instance of the object is automatically created in the global namespace when the script engine is initialized. That instance is accessible via Global::Math. Additional instances of the object cannot be created. See the ECMA script specification for more information. Todo Examples:
 */
declare class Math {
    E(): number;
    LN10: number;
    LN2: number;
    LOG10E: number;
    LOG2E: number;
    PI: number;
    SQRT1_2: number;
    SQRT2: number;

    abs(num: number): number;
    acos(num: number): number;
    asin(num: number): number;
    atan(num: number): number;
    atan2(yCoord: number, xCoord: number): number;
    ceil(num: number): number;
    cos(num: number): number;
    exp(num: number): number;
    floor(num: number): number;
    log(num: number): number;
    max(num1: number, num2: number): number;
    min(num1: number, num2: number): number;
    pow(num: number, power: number): number;
    random(): number;
    round(num: number): number;
    sin(num: number): number;
    sqrt(num: number): number;
    tan(num: number): number;
}

/**
 * A transformation matrix consisting of 4 rows and 3 columns.
 */
declare class DzMatrix3 {
    isIdentity(): boolean;
    m11: number;
    m12: number;
    m13: number;
    m14: number;
    m21: number;
    m22: number;
    m23: number;
    m24: number;
    m31: number;
    m32: number;
    m33: number;
    m34: number;

    det3(): number;
    inverse(): DzMatrix3;
    makeIdentity(): void;
    matrix4(): DzMatrix4;
    multiply(mat: DzMatrix3): DzMatrix3;
    multMatrixVec(vec: DzVec3): DzVec3;
    multVec(vec: DzVec3): DzVec3;
    noRot(): void;
    noScale(): void;
    noTrans(): void;
    orthogonal(): boolean;
    orthogonalize(): void;
    preRotate(rot: DzQuat): void;
    preRotateX(radians: number): void;
    preRotateY(radians: number): void;
    preRotateZ(radians: number): void;
    preTranslate(vec: DzVec3): void;
    rotate(rot: DzQuat): void;
    rotateX(radians: number): void;
    rotateY(radians: number): void;
    rotateZ(radians: number): void;
    row(i: number): DzVec3;
    scale(scale: number, direction: DzVec3, affectTrans: boolean): void;
    scale(vec: DzVec3, affectTrans: boolean): void;
    scale(scale: number, affectTrans: boolean): void;
    setTrans(vec: DzVec3): void;
    shearXY(xShear: number, yShear: number): void;
    shearXZ(xShear: number, zShear: number): void;
    shearYZ(yShear: number, zShear: number): void;
    toString(): string;
    trace(): number;
    translate(vec: DzVec3): void;
}

/**
 * A transformation matrix consisting of 4 rows and 4 columns.
 */
declare class DzMatrix4 {
    isIdentity(): boolean;
    m11: number;
    m12: number;
    m13: number;
    m14: number;
    m21: number;
    m22: number;
    m23: number;
    m24: number;
    m31: number;
    m32: number;
    m33: number;
    m34: number;
    m41: number;
    m42: number;
    m43: number;
    m44: number;

    inverse(): DzMatrix4;
    invert(): void;
    makeIdentity(): void;
    matrix3(): DzMatrix3;
    multiply(mat: DzMatrix4): DzMatrix4;
    multMatrixVec(vec: DzVec3): DzVec3;
    multVecMatrix(vec: DzVec3): DzVec3;
    orthogonal(): boolean;
    preScale(scale: number): void;
    preScale(vec: DzVec3): void;
    preScale(scale: number, direction: DzVec3): void;
    preShearXY(xShear: number, yShear: number): void;
    preShearXZ(xShear: number, zShear: number): void;
    preShearYZ(yShear: number, zShear: number): void;
    preTranslate(vec: DzVec3): void;
    rotate(rot: DzQuat): void;
    rotateX(radians: number): void;
    rotateY(radians: number): void;
    rotateZ(radians: number): void;
    row(i: number): DzVec3;
    scale(scale: number, direction: DzVec3): void;
    scale(vec: DzVec3): void;
    scale(scale: number): void;
    setRow(i: number, vec: DzVec3): void;
    setTrans(vec: DzVec3): void;
    shearXY(xShear: number, yShear: number): void;
    shearXZ(xShear: number, zShear: number): void;
    shearYZ(yShear: number, zShear: number): void;
    toString(): string;
    trace(): number;
    translate(vec: DzVec3): void;
    transpose(): DzMatrix4;
}

/**
 * TODO: Add detailed description.
 */
declare class DzMenu {
    addAction(action: DzAction, menuId: number): number;
    addAction(className: string, menuId: number): number;
    addItem(label: string, menuId: number): number;
    addItem(label: string, receiver: QObject, member: string, menuId: number): number;
    addSeparator(menuId: number): void;
    addSubMenu(label: string, menuId: number): number;
    exec(pos: Point): number;
    findSubMenu(label: string, menuId: number): number;
    isEmpty(): boolean;
    setItemCheckable(itemId: number, checkable: boolean): void;
    setItemChecked(itemId: number, checked: boolean): void;
    setItemData(itemId: number, data: any): void;
    setItemEnabled(itemId: number, enabled: boolean): void;

    // SIGNALS
    activated(id: number): void;
}

/**
 * Attention: This class will eventually be merged with DzModifier . Since: 4.9.2.1
 */
declare class DzMeshModifier {
    assetAuthor(): DzAuthor;
    assetFileRevision: DzVersion;
    assetId: string;
    assetModifiedDate: Date;
    assetNeedSave: boolean;
    assetSource: DzUri;
    assetUri: DzUri;

    canLoadFromAutoLocation(): boolean;
    modifyAsset(): boolean;
    modifyAsset(newUri: DzUri): boolean;

    // SIGNALS
    assetModified(): void;
    assetWasSaved(): void;
}

/**
 * A specialization of DzModifier that iteratively applies a smoothing algorithm to the position of vertices in the geometry of an object with this modifier, and (potentially) iteratively detects/corrects collisions that occur between it and the geometry of another object as a result of the smoothing.
 */
declare class DzMeshSmoothModifier {
    assetAuthor(): DzAuthor;
    assetFileRevision: DzVersion;
    assetId: string;
    assetModifiedDate: Date;
    assetNeedSave: boolean;
    assetSource: DzUri;
    assetUri: DzUri;

    getCollisionItem(): DzNode;
    getCollisionIterationControl(): DzIntProperty;
    getCollisionNodeControl(): DzNodeProperty;
    getCollisionSmoothingIntervalControl(): DzIntProperty;
    getEnableSmoothingControl(): DzBoolProperty;
    getInteractiveUpdateControl(): DzBoolProperty;
    getLengthInfluenceControl(): DzFloatProperty;
    getLockDistanceControl(): DzFloatProperty;
    getSecondaryWeightControl(): DzFloatProperty;
    getSmoothingIterationsControl(): DzIntProperty;
    getSmoothingTypeControl(): DzEnumProperty;
    getWeightControl(): DzFloatProperty;
    modifyAsset(): boolean;
    setCollisionItem(item: DzNode): void;

    // SIGNALS
    assetModified(): void;
    assetWasSaved(): void;
}

/**
 * A global static object available via the Global :: MessageBox variable. This object provides functions that display pre-built message boxes to the user. This is the easiest way for a script to interact with a user - simply call one of the functions as shown in the following examples: Example: Display an information box with an 'Ok' button Example: Ask the user a question with 'Yes'/'No' buttons Example: Display a warning message to the user Example: Display a critical message to the user
 */
declare class DzMessageBox {
    critical(text: string, title: string, button0: string, button1: string, button2: string): number;
    information(text: string, title: string, button0: string, button1: string, button2: string): number;
    question(text: string, title: string, button0: string, button1: string, button2: string): number;
    warning(text: string, title: string, button0: string, button1: string, button2: string): number;
}

/**
 * See Also: DzObject :: addModifier () DzObject :: removeModifier () DzObject :: moveModifier () DzObject :: removeAllModifiers ()
 */
declare class DzModifier {
    getAssignedModifierStackSectionID(): number;
    getPreferredModifierStackSectionID(): number;
    getUnknownModifierStackSectionID(): number;

    // SIGNALS
    aboutToBeRemoved(): void;
    added(): void;
    currentValueChanged(): void;
    removed(): void;
}

/**
 * An asset save filter for saving Modifier Support Asset(s) in the DSON format. See Also: Sample: Save Modifier Support Asset(s) Since: 4.22.1.97
 */
declare class DzModifierSupportAssetFilter {
}

/**
 * Sometimes referred to as a “morph target”, a “blendshape”, or a “shape key”, a morph is a specialization of DzModifier that moves the position of vertices in the geometry of an object in discrete directions in order to produce a pre-defined shape. The pre-defined shape is defined relative to the base shape of the object, in local space, and is applied according to a weight that is supplied by a value control. This weight defines the amplitude by which a given vertex in the morph is linearly moved along the vector created between its position in the base shape of the object and its position in the pre-defined shape. See Also: DzObject :: findModifier () DzMorphDeltas
 */
declare class DzMorph {
    assetAuthor(): DzAuthor;
    assetFileRevision: DzVersion;
    assetId: string;
    assetModifiedDate: Date;
    assetNeedSave: boolean;
    assetSource: DzUri;
    assetUri: DzUri;

    clearDeltasOnVertexSelection(mesh: DzVertexMesh, selected: boolean, writeToStatusLine: boolean): DzError;
    getDeltas(): DzMorphDeltas;
    getHDLimit(): number;
    getValueControl(): DzFloatProperty;
    modifyAsset(newUri: DzUri): boolean;
    modifyAsset(): boolean;
    setDeltas(deltas: DzMorphDeltas): void;
    setHDLimit(limit: number): void;
    getValueChannel(): DzFloatProperty;

    // SIGNALS
    assetModified(): void;
    assetWasSaved(): void;
    deltasChanged(): void;
    hdLimitChanged(): void;
}

/**
 * A container for a discrete list of three dimensional position changes (deltas) to the vertices of a mesh, for a morph. See Also: DzMorph
 */
declare class DzMorphDeltas {
    calculateDeltas(srcGeom: DzVertexMesh, tgtGeom: DzVertexMesh, tolerance: number): DzMorphDeltas;
    addDelta(vertIdx: number, delta: DzVec3, checkForDuplicates: boolean): number;
    addDelta(vertIdx: number, deltaX: number, deltaY: number, deltaZ: number, checkForDuplicates: boolean): number;
    copyDeltas(): DzMorphDeltas;
    copyDeltasTo(deltas: DzMorphDeltas): void;
    getDeltaIndex(i: number): number;
    getDeltaVec(i: number): DzVec3;
    getNumDeltas(): number;
    getTargetVertexCount(): number;
    getVertexDeltaIndex(vertIdx: number): number;
    hasDeltas(): boolean;
    loadDeltas(): boolean;
    preSize(nDeltas: number): void;
    removeAllDeltas(): void;
    removeDelta(deltaIdx: number): void;
    removeDuplicateDeltas(): void;
    removeIgnoredDeltas(): DzMorphDeltas;
    removeVertex(vertIdx: number): void;
    setDelta(index: number, delta: DzVec3): DzError;
    setTargetVertexCount(vertCount: number): void;
    unLoadDeltas(): void;
    setVertCount(vertCount: number): void;
    getVertCount(): number;

    // SIGNALS
    deltaListChanged(): void;
    deltaListLoaded(): void;
    deltaValueChanged(): void;
}

/**
 * Since: 4.9.3.46 Attention: This object is provided by the Morph Loader Pro plugin. It is only available when the Morph Loader Pro plugin is activated and enabled. See Also: DzMorphLoaderBatch Sample: Silent OBJ Morph Loader Import
 */
declare class DzMorphLoader {
    getPathForContext(context: DzWeightMapContext, node: DzNode): string;
    applyReverseDeformationsPose(): boolean;
    createMorph(settings: DzFileIOSettings, node: DzNode, onlyErrorsOrWarnings: boolean, plainText: boolean): string;
    createMorphFromMesh(mesh: DzVertexMesh, node: DzNode, onlyErrorsOrWarnings: boolean, plainText: boolean): string;
    getAttenuateEdgeStrength(): number;
    getAttenuateMapPath(): string;
    getAttenuateStrength(): number;
    getCleanUpOrphans(): boolean;
    getControlNode(): DzNode;
    getControlProperty(): DzNumericProperty;
    getControlPropertyCustomLabel(): string;
    getControlPropertyERCCustomValue(): number;
    getControlPropertyERCType(): ERCType;
    getControlPropertyERCUseCustomValue(): boolean;
    getControlPropertyUseCustomLabel(): boolean;
    getCreateControlProperty(): boolean;
    getDeltaTolerance(): number;
    getDisplayName(): string;
    getFilename(): string;
    getHideSecondaryProperties(): boolean;
    getMorphMirroring(): MirroringType;
    getMorphName(): string;
    getOverwriteExisting(): OverwriteMode;
    getPreserveExistingDeltas(): boolean;
    getPropertyGroupPath(): string;
    getReverseDeformations(): boolean;
    getReverseDeformationsPose(): string;
    morphAlreadyExists(node: DzNode): boolean;
    readObjectCommonSettingsFromConfigFile(filename: string): boolean;
    readObjectSettingsFromConfigFile(filename: string, filePath: string): boolean;
    saveObjectSettingsToConfigFile(filename: string, projectPath: string, saveProjectRelative: boolean): boolean;
    setAttenuateEdgeStrength(val: number): void;
    setAttenuateMapPath(mapPath: string): void;
    setAttenuateStrength(val: number): void;
    setCleanUpOrphans(onOff: boolean): void;
    setControlNode(node: DzNode): void;
    setControlProperty(prop: DzNumericProperty): void;
    setControlPropertyCustomLabel(label: string): void;
    setControlPropertyERCCustomValue(val: number): void;
    setControlPropertyERCType(type: ERCType): void;
    setControlPropertyERCUseCustomValue(onOff: boolean): void;
    setControlPropertyUseCustomLabel(onOff: boolean): void;
    setCreateControlProperty(onOff: boolean): void;
    setDeltaTolerance(val: number): void;
    setDisplayName(name: string): void;
    setFilename(filename: string): void;
    setHideSecondaryProperties(onOff: boolean): void;
    setLoadMode(mode: LoadMode, node: DzNode): bool;
    setMorphMirroring(type: MirroringType): void;
    setMorphName(name: string): void;
    setOverwriteExisting(mode: OverwriteMode): void;
    setPreserveExistingDeltas(onOff: boolean): void;
    setPropertyGroupPath(path: string): void;
    setReverseDeformations(onOff: boolean): void;
    setReverseDeformationsPose(filePath: string): void;

    // SIGNALS
    applyAfterJointChanged(onOff: boolean): void;
    attenuateChanged(): void;
    attenuateEdgeStrengthChanged(strength: number): void;
    attenuateStrengthChanged(strength: number): void;
    controlNodeChanged(node: DzNode): void;
    controlPropertyChanged(prop: DzNumericProperty): void;
    createControlPropertyChanged(onOff: boolean): void;
    deltaToleranceChanged(val: number): void;
    ercCustomValueChanged(val: number): void;
    filenameChanged(name: string): void;
    hideSecondaryChanged(onOff: boolean): void;
    mirroringChanged(mirroring: MirroringType): void;
    morphNameChanged(name: string): void;
    overwriteExistingChanged(value: OverwriteMode): void;
    preserveExistingDeltasChanged(onOff: boolean): void;
    propertyGroupPathChanged(path: string): void;
    reverseDeformationsChanged(onOff: boolean): void;
    secondaryLabelChanged(label: string): void;
    useErcCustomValueChanged(onOff: boolean): void;
    useSecondaryLabelChanged(onOff: boolean): void;
}

/**
 * Implements a batch of morph loader objects that will be applied to the same node(s). Since: 4.9.3.46 Attention: This object is provided by the Morph Loader Pro plugin. It is only available when the Morph Loader Pro plugin is activated and enabled. See Also: DzMorphLoader Sample: Silent OBJ Morph Loader Import
 */
declare class DzMorphLoaderBatch {
    addFromConfigFile(filename: string): void;
    addFromFile(file: string): void;
    addFromFiles(files: any[]): void;
    addFromMesh(mesh: DzVertexMesh): void;
    addMorph(morph: DzMorphLoader): void;
    clear(): void;
    createMorphs(settings: DzFileIOSettings, node: DzNode, onlyErrorsOrWarnings: boolean, plainText: boolean): string;
    createMorphsFromMesh(mesh: DzVertexMesh, node: DzNode, onlyErrorsOrWarnings: boolean, plainText: boolean): string;
    findMorph(morph: DzMorphLoader): number;
    getMorph(index: number): DzMorphLoader;
    getNode(): DzNode;
    getNumMorphs(): number;
    moveMorph(morph: DzMorphLoader, upDown: boolean): void;
    presetConfigurationFile(): string;
    removeMorph(morph: DzMorphLoader): void;
    saveProjectSettingsToConfigFile(filename: string, saveRelative: boolean, saveObjects: boolean): boolean;
    setNode(node: DzNode): void;
    setPresetConfigurationFile(filename: string): void;
    setUsePresetConfiguration(onOff: boolean): void;
    usePresetConfiguration(): boolean;

    // SIGNALS
    morphAdded(morph: DzMorphLoader): void;
    morphListChanged(): void;
    morphMoved(srcIdx: number, destIdx: number): void;
    morphRemoved(morph: DzMorphLoader, formerIndex: number): void;
}

/**
 * Deprecated Exists only to keep old code working. Do not use in new code. Use DzModifierSupportAssetFilter instead.
 */
declare class DzMorphSupportAssetFilter {
}

/**
 * Responsible for the management of multimedia (audio/video) exporters/importers. There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getMultiMediaMgr (). See Also: Global :: App DzAudioImporter DzAudioClip DzVideoExporter DzVideoClip
 */
declare class DzMultiMediaMgr {
    findAudioImporter(filename: string): DzAudioImporter;
    findVideoExporter(filename: string): DzVideoExporter;
    getAudioImporter(i: number): DzAudioImporter;
    getNumAudioImporters(): number;
    getNumVideoExporters(): number;
    getVideoExporter(i: number): DzVideoExporter;
    makeAudioImportFileFilter(filter: DzFileFilter, defaultFilter: string, makeAllFilesEntry: boolean): void;
    makeVideoExportFileFilter(filter: DzFileFilter, defaultFilter: string): void;
    exportVideoClip(fileName: string, clip: DzVideoClip, exporterIndex: number): DzError;
    getAudioClipLoadPath(): string;
    getVideoClipSavePath(): string;
    importAudioClip(fileName: string, clip: DzAudioClip, importerIndex: number): DzError;
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureLayer :: BlendMultiply instead.
 */
declare class DzMultiplyBlend {
}

/**
 * When the interpreter detects a runtime error, it throws an instance of one of the NativeError objects. The native error objects differ only in their type and in the implementation-defined value of the message property of the prototype object. See the ECMA script specification for more information.
 */
declare class NativeError {
}

/**
 * DzNode objects all contain animatable position, rotation, and scale channels that can be set and accessed via the properties list in the DzElement class or through specialized calls in this class. The transform order is Translate/Rotate/Scale. Non-uniform scaling is supported by implementing separate X, Y, and Z scale channels. All channels are independent internally and can have keys set on them independent of any other channel. Note that channel independence holds exactly true for translations and scales, but does not hold true for rotations (which are represented to the user as Euler angle degrees for each axis channel). Euler angles are inherently inter-dependent and prone to numerical singularities (“gimbal lock”) that make them less than perfect at representing rotations. For this reason, rotations are handled as DzQuat objects (quaternions) whenever possible. When setting keys on a DzNode , it is preferable to use the set*Rot () methods or set*Transform () methods that take DzQuat arguments. Setting rotations as a DzQuat will create keys on all three rotation channels but will assure that the values are reasonable. Each node defines an order that axis rotations will be applied in for the node. The order defined is important as it serves to avoid numerical singularities (“gimbal lock”). The rotation order of a node should be defined such that the first axis in the order is the primary axis - the axis that the node will twist along. The second axis in the order should be defined as the axis where rotations are least likely to reach 90°. And the third axis in the order should be defined as the axis where rotations are most likely to reach 90°. Nodes have an origin and an orientation that define the base position and rotation of its “local space,” that is - a base from which a node's transformations can be expressed in relative terms. The origin defines the point around which a node rotates, the point around which a node is scaled, the point from which a node's translation is relative. In other words, the origin is the definition of an adjusted “center” point“ (a positional offset) for the node. The origin of a node is defined in non-transformed world space coordinates. The orientation of a node defines the base rotation (a rotational offset) that a node's rotations are expressed as being relative to. Adjusting the orientation of a node has an effect on the rotation and the scale of a node, it does not affect the translation of a node. Several functions are provided for accessing the transformation data of a node. Below are descriptions of the groups of functions, and the transform space that they return data for. World Space Transforms: getWSTransform (), getWSPos (), getWSRot (), getWSScale (). WS (world space) transforms are just that - the transformation of the node into world space, including keyed transformation data. These functions essentially traverse up the hierarchy evaluating the local transforms for each parent node, resulting in the final world space transform of the node. Local Transforms: getLocalTransform (), getLocalPos (), getLocalRot (), getLocalScale (). Local transforms are the full transformation of the node in the space of its immediate parent - for root nodes, the node's origin added to the local position is equivalent to the world space transform.
 */
declare class DzNode {
    assetAuthor(): DzAuthor;
    assetFileRevision: DzVersion;
    assetId: string;
    assetIdAliases: any[];
    assetModifiedDate: Date;
    assetNeedSave: boolean;
    assetSource: DzUri;
    assetUri: DzUri;
    extendedAddonsPath: string;
    extendedAssetIds: string;
    nameAliases: any[];
    renderPriority: RenderPriority;

    duplicate(node: DzNode, propagate: boolean): DzNode;
    addNodeChild(child: DzNode, inPlace: boolean): DzError;
    adjustEndPoint(endPnt: DzVec3): void;
    adjustOrientation(orientation: DzQuat): void;
    adjustOrientationAngles(angles: DzVec3): void;
    adjustOrigin(origin: DzVec3): void;
    calcLocalRotation(anglesRadians: DzVec3): DzQuat;
    castsShadow(): boolean;
    clearAllTransformData(): void;
    clearManipOverColor(): void;
    clearTransformData(range: DzTimeRange): void;
    duplicate(propagate: boolean): DzNode;
    finalize(isRender: boolean, allowResChange: boolean): void;
    findChildIndex(node: DzNode): number;
    findNodeChild(name: string, recurse: boolean): DzNode;
    findNodeChildByAssetID(assetID: string, recurse: boolean, checkSource: boolean): DzNode;
    findNodeChildByLabel(label: string, recurse: boolean): DzNode;
    findNodeChildByNameOrAlias(name: string, aliases: boolean, recurse: boolean): DzNode;
    findPropertyReference(uri: DzUri): DzProperty;
    getDisableTransformControl(): DzBoolProperty;
    getEndPoint(defaultVal: boolean): DzVec3;
    getEndXControl(): DzFloatProperty;
    getEndYControl(): DzFloatProperty;
    getEndZControl(): DzFloatProperty;
    getFirstAxisRotControl(): DzFloatProperty;
    getIgnoreLocalTransformControl(): DzBoolProperty;
    getLocalBoundingBox(): DzBox3;
    getLocalOrientedBox(): DzOrientedBox3;
    getLocalPos(): DzVec3;
    getLocalPos(tm: number, defaultVal: boolean): DzVec3;
    getLocalRot(): DzQuat;
    getLocalRot(tm: number, defaultVal: boolean): DzQuat;
    getLocalScale(): DzMatrix3;
    getLocalScale(tm: number, defaultVal: boolean): DzMatrix3;
    getLocalTransform(): DzMatrix3;
    getLocalTransform(tm: number, defaultVal: boolean): DzMatrix3;
    getLocalTransformAxisValues(posLocal: DzVec3, rotLocal: DzQuat, scaleLocal: DzMatrix3): any;
    getNodeChild(i: number): DzNode;
    getNodeChildren(recurse: boolean): any[];
    getNodeParent(): DzNode;
    getNumNodeChildren(): number;
    getObject(): DzObject;
    getOrientation(defaultVal: boolean): DzQuat;
    getOrientXControl(): DzFloatProperty;
    getOrientYControl(): DzFloatProperty;
    getOrientZControl(): DzFloatProperty;
    getOrigin(defaultVal: boolean): DzVec3;
    getOriginXControl(): DzFloatProperty;
    getOriginYControl(): DzFloatProperty;
    getOriginZControl(): DzFloatProperty;
    getPointAtControl(): DzNumericNodeProperty;
    getPointAtStrength(): number;
    getPointAtTarget(): DzNode;
    getPresentation(): DzPresentation;
    getPreviewBox(): DzOrientedBox3;
    getRenderPriorityControl(): DzEnumProperty;
    getRenderVisibilityControl(): DzBoolProperty;
    getRotationOrder(): DzRotationOrder;
    getScaleControl(): DzFloatProperty;
    getSecondAxisRotControl(): DzFloatProperty;
    getSelectabilityControl(): DzBoolProperty;
    getSelectionMap(): DzSelectionMap;
    getSelectionNode(): DzNode;
    getShadowControl(): DzBoolProperty;
    getSimulationVisibilityControl(): DzBoolProperty;
    getSingletonIDString(): string;
    getSkeleton(): DzSkeleton;
    getThirdAxisRotControl(): DzFloatProperty;
    getToolFirstAxisRotControl(): DzFloatProperty;
    getToolLocalRot(): DzQuat;
    getToolLocalRot(tm: number, defaultVal: boolean): DzQuat;
    getToolSecondAxisRotControl(): DzFloatProperty;
    getToolThirdAxisRotControl(): DzFloatProperty;
    getToolWSRot(tm: number, defaultVal: boolean): DzQuat;
    getToolWSRot(): DzQuat;
    getToolWSTransform(): DzMatrix3;
    getToolWSTransform(tm: number, defaultVal: boolean): DzMatrix3;
    getToolXRotControl(): DzFloatProperty;
    getToolYRotControl(): DzFloatProperty;
    getToolZRotControl(): DzFloatProperty;
    getViewportVisibilityControl(): DzBoolProperty;
    getVisibilityControl(): DzBoolProperty;
    getWSBoundingBox(): DzBox3;
    getWSOrientedBox(): DzOrientedBox3;
    getWSPos(): DzVec3;
    getWSPos(tm: number, defaultVal: boolean): DzVec3;
    getWSRot(): DzQuat;
    getWSRot(tm: number, defaultVal: boolean): DzQuat;
    getWSScale(): DzMatrix3;
    getWSScale(tm: number, defaultVal: boolean): DzMatrix3;
    getWSTransform(): DzMatrix3;
    getWSTransform(tm: number, defaultVal: boolean): DzMatrix3;
    getWSTransformAxisValues(posLocal: DzVec3, rotLocal: DzQuat, scaleLocal: DzMatrix3): any;
    getWSTransformAxisValues(tm: number, posLocal: DzVec3, rotLocal: DzQuat, scaleLocal: DzMatrix3): any;
    getXPosControl(): DzFloatProperty;
    getXRotControl(): DzFloatProperty;
    getXScaleControl(): DzFloatProperty;
    getYPosControl(): DzFloatProperty;
    getYRotControl(): DzFloatProperty;
    getYScaleControl(): DzFloatProperty;
    getZPosControl(): DzFloatProperty;
    getZRotControl(): DzFloatProperty;
    getZScaleControl(): DzFloatProperty;
    inheritsScale(): boolean;
    invalidateBoundingBoxes(checkSkeleton: boolean): void;
    invisibleByGroup(): boolean;
    invisibleInRenderByGroup(): boolean;
    invisibleInSimulationByGroup(): boolean;
    invisibleInViewportByGroup(): boolean;
    isBoneSelectingNode(): boolean;
    isEditorNode(): boolean;
    isHidden(): boolean;
    isInScene(): boolean;
    isLocalTransformDisabled(): boolean;
    isLocalTransformIgnored(): boolean;
    isNodeAncestorOf(node: DzNode, recurse: boolean): boolean;
    isNodeChild(node: DzNode): boolean;
    isNodeDescendantOf(node: DzNode, recurse: boolean): boolean;
    isRootNode(): boolean;
    isSelectable(): boolean;
    isSelected(): boolean;
    isSelectionPromoted(): boolean;
    isVisible(): boolean;
    isVisibleInRender(): boolean;
    isVisibleInSimulation(): boolean;
    isVisibleInViewport(): boolean;
    modifyAsset(): boolean;
    modifyAsset(newUri: DzUri): boolean;
    moveNodeChildToIndex(childIndex: number, newChildIndex: number): DzError;
    moveNodeChildToIndex(child: DzNode, index: number): DzError;
    removeAllNodeChildren(): void;
    removeNodeChild(child: DzNode, inPlace: boolean): DzError;
    select(onOff: boolean): void;
    setEndPoint(endPnt: DzVec3, makeDefault: boolean): void;
    setHidden(onOff: boolean): void;
    setInheritScale(onOff: boolean): void;
    setInvisibleByGroup(yesNo: boolean): void;
    setInvisibleInRenderByGroup(yesNo: boolean): void;
    setInvisibleInSimulationByGroup(yesNo: boolean): void;
    setInvisibleInViewportByGroup(yesNo: boolean): void;
    setLocalPos(posLocal: DzVec3): void;
    setLocalPos(tm: number, posLocal: DzVec3): void;
    setLocalRot(rotLocal: DzQuat): void;
    setLocalRot(tm: number, rotLocal: DzQuat): void;
    setLocalScale(tm: number, scaleLocal: DzMatrix3): void;
    setLocalScale(scaleLocal: DzMatrix3, generalScale: number): void;
    setLocalScale(tm: number, scaleLocal: DzMatrix3, generalScale: number): void;
    setLocalScale(scaleLocal: DzMatrix3): void;
    setLocalTransform(posLocal: DzVec3, rotLocal: DzQuat, scaleLocal: DzMatrix3): void;
    setLocalTransform(tm: number, posLocal: DzVec3, rotLocal: DzQuat, scaleLocal: DzMatrix3): void;
    setLocalTransform(posLocal: DzVec3, rotLocal: DzQuat, scaleLocal: DzMatrix3, generalScale: number): void;
    setLocalTransform(tm: number, posLocal: DzVec3, rotLocal: DzQuat, scaleLocal: DzMatrix3, generalScale: number): void;
    setLocalTransformDisabled(onOff: boolean): void;
    setLocalTransformIgnored(onOff: boolean): void;
    setManipOverColor(color: { r: number, g: number, b: number, a: number }): void;
    setObject(object: DzObject): void;
    setOrientation(orientation: DzQuat, makeDefault: boolean): void;
    setOrientationAngles(angles: DzVec3, makeDefault: boolean): void;
    setOrigin(origin: DzVec3, makeDefault: boolean): void;
    setPointAtStrength(strength: number): void;
    setPointAtTarget(target: DzNode): void;
    setPresentation(pres: DzPresentation): void;
    setPreviewBox(box: DzOrientedBox3): void;
    setPromoteSelection(onOff: boolean): void;
    setRotationOrder(order: DzRotationOrder): void;
    setSelectable(onOff: boolean): void;
    setSelectionMap(map: DzSelectionMap): void;
    setToolLocalRot(tm: number, rotLocal: DzQuat): void;
    setToolLocalRot(rotLocal: DzQuat): void;
    setToolLocalTransform(posLocal: DzVec3, rotLocal: DzQuat, scaleLocal: DzMatrix3, generalScale: number): void;
    setToolLocalTransform(posLocal: DzVec3, rotLocal: DzQuat, scaleLocal: DzMatrix3): void;
    setToolLocalTransform(tm: number, posLocal: DzVec3, rotLocal: DzQuat, scaleLocal: DzMatrix3, generalScale: number): void;
    setToolLocalTransform(tm: number, posLocal: DzVec3, rotLocal: DzQuat, scaleLocal: DzMatrix3): void;
    setToolWSRot(rotWS: DzQuat): void;
    setToolWSRot(tm: number, rotWS: DzQuat): void;
    setToolWSTransform(posWS: DzVec3, rotWS: DzQuat, scaleWS: DzMatrix3): void;
    setToolWSTransform(tm: number, posWS: DzVec3, rotWS: DzQuat, scaleWS: DzMatrix3): void;
    setUnselectableByGroup(yesNo: boolean): void;
    setVisible(onOff: boolean): void;
    setVisibleInRender(onOff: boolean): void;
    setVisibleInSimulation(onOff: boolean): void;
    setVisibleInViewport(onOff: boolean): void;
    setWSPos(posWS: DzVec3): void;
    setWSPos(tm: number, posWS: DzVec3): void;
    setWSRot(rotWS: DzQuat): void;
    setWSRot(tm: number, rotWS: DzQuat): void;
    setWSScale(tm: number, scaleWS: DzMatrix3): void;
    setWSScale(scaleWS: DzMatrix3): void;
    setWSTransform(posWS: DzVec3, rotWS: DzQuat, scaleWS: DzMatrix3): void;
    setWSTransform(tm: number, posWS: DzVec3, rotWS: DzQuat, scaleWS: DzMatrix3): void;
    unselectableByGroup(): boolean;
    update(isRender: boolean): void;
    updateOrientation(): void;

    // SIGNALS
    aboutToBeRemoved(): void;
    aboutToDelete(node: DzNode): void;
    added(): void;
    assetModified(): void;
    assetWasSaved(): void;
    boundBoxInvalidated(): void;
    childAdded(child: DzNode): void;
    childListChanged(): void;
    childListOrderChanged(): void;
    childRemoved(child: DzNode): void;
    drawnDataChanged(): void;
    hiddenChanged(hidden: boolean): void;
    inheritScaleChanged(): void;
    materialListChanged(): void;
    materialSelectionChanged(): void;
    materialSelectionSetsChanged(): void;
    objectChanged(node: DzNode, oldObject: DzObject, newObject: DzObject): void;
    parentChanged(node: DzNode, oldParent: DzNode, newParent: DzNode): void;
    parentHierarchyChanged(node: DzNode): void;
    promoteSelectionChanged(promoteSelection: boolean): void;
    removed(): void;
    riggingChanged(): void;
    rotationOrderChanged(): void;
    selectabilityChanged(): void;
    selected(node: DzNode, onOff: boolean): void;
    topologyChanged(): void;
    transformChanged(): void;
    uvsChanged(): void;
    visibilityChanged(): void;
    visibilityInRenderChanged(): void;
    visibilityInSimulationChanged(): void;
    visibilityInViewportChanged(): void;
}

/**
 * See Also: Sample: Node Align Attention: This object is provided by the Align pane plugin. It is only available when the Align pane plugin is activated and enabled. Since: 4.10.0.122
 */
declare class DzNodeAligner {
    addNode(node: DzNode): DzError;
    canAlign(): boolean;
    clearNodes(): void;
    doAlign(): boolean;
    getNodes(): any[];
    getXAlign(): AlignX;
    getXUnits(size: UnitSize): number;
    getXUseInterval(): boolean;
    getYAlign(): AlignY;
    getYUnits(size: UnitSize): number;
    getYUseInterval(): boolean;
    getZAlign(): AlignZ;
    getZUnits(size: UnitSize): number;
    getZUseInterval(): boolean;
    setXAlign(align: AlignX): void;
    setXUnits(units: number, size: UnitSize): void;
    setXUseInterval(onOff: boolean): void;
    setYAlign(align: AlignY): void;
    setYUnits(units: number, size: UnitSize): void;
    setYUseInterval(onOff: boolean): void;
    setZAlign(align: AlignZ): void;
    setZUnits(units: number, size: UnitSize): void;
    setZUseInterval(onOff: boolean): void;

    // SIGNALS
    canAlignChanged(onOff: boolean): void;
}

/**
 * An animatable property whose value is a choice of one of the node objects in the current scene, or none. Instead of tracking a numeric value, this property maintains a pointer to another node in the scene. Use this property when you need an element to track a user-selected scene node; for example, this property could be used in a node to allow the user to select another node in the scene to follow, or it could be used by a modifier that uses a node in the scene to determine how it is applied, etc.
 */
declare class DzNodeProperty {
    exclude(node: DzNode): void;
    getDefaultValue(): DzNode;
    getKeyValue(i: number): DzNode;
    getValue(tm: number): DzNode;
    getValue(): DzNode;
    isExcluded(node: DzNode): boolean;
    setDefaultValue(node: DzNode): void;
    setKeyValue(which: number, node: DzNode): void;
    setValue(node: DzNode): void;
    setValue(tm: number, node: DzNode): void;
    unexclude(node: DzNode): void;

    // SIGNALS
    aboutToChange(): void;
}

/**
 * Provides a DzComboBox like widget with a custom popup designed for choosing a DzNode .
 */
declare class DzNodeSelectionComboBox {
    clearNodeSelection(): void;
    getNodes(): any[];
    getSelectedNode(): DzNode;
    hidePopup(): void;
    setNode(node: DzNode): void;
    setNodes(nodes: any[]): void;
    setSelectedNode(node: DzNode): void;
    showPopup(): void;

    // SIGNALS
    nodeSelectionChanged(): void;
}

/**
 * An asset save filter for saving Figure or Prop Support Assets in the DSON format. See Also: Sample: Save Figure/Prop Support Assets
 */
declare class DzNodeSupportAssetFilter {
    getSetNode(): DzNode;
    setNode(node: DzNode): void;
}

/**
 * A special type of “Asset” that allows a “Product” that has not been installed to be displayed within an assset view.
 */
declare class DzNotInstalledProductAsset {
    installFromCloud(): void;
    loadIcon(): void;
}

/**
 * This is the only numeric type in DAZScript. When a script is interacting with classes from the SDK, all the C++ numeric types (int, float, double, etc) are converted to/from this type. Numbers are not typically constructed, rather they are created by simple assignment. Example:
 */
declare class Number {
    MAX_VALUE(): number;
    MIN_VALUE: number;
    NaN: number;
    NEGATIVE_INFINITY: number;
    POSITIVE_INFINITY: number;

    toExponential(fractionDigits: number): string;
    toFixed(fractionDigits: number): string;
    toLocaleString(): string;
    toPrecision(precision: number): string;
    toString(radix: number): string;
    toString(): string;
}

/**
 * This is the base class for all controllers that can control the value of a DzNumericProperty-derived object. DzNumericProperty objects can have multiple controllers, these controllers are applied in the order they appear in the controller list. The application of controllers in a DzNumeric-derived property begins with the keyed (raw) value of the property at the given time, this is the value that is passed to the apply () function of the first controller. The result returned by the apply () call to the first controller is then passed into the apply () function on the second controller, and so on. The result returned by the apply () function of the last controller on the property is then returned as the final value of the property for the given time. The applyInverse function is used to determine the keyed (raw) value of the property when the user enters a number for the final value of the property. Controllers which have an 'Additive' effect must reimplement this method so that the value of the property appears to respond correctly to user input. Controllers which have a 'Replace' effect need not reimplement this function, since they have no inverse because they do not use the raw value of the property in their calculation.
 */
declare class DzNumericController {
    apply(val: number, tm: number, local: boolean): number;
    applyInverse(val: number, tm: number, local: boolean): number;
}

/**
 * This property tracks both a numeric value and a node value - it is essentially a combination of a DzFloatProperty and a DzNodeProperty in a single property. The main benefit of this is to display the settings to the user as a single parameter, it also provides several conveniences for the programmer in linking the two values together. Currently, this property is used by DzNode to implement the 'Point At' parameter.
 */
declare class DzNumericNodeProperty {
    getNode(): DzNode;
    isInvalidWithoutNode(): boolean;
    setMustHaveNode(onOff: boolean): void;
    setNode(node: DzNode): void;

    // SIGNALS
    invalidWithoutNodeChanged(onOff: boolean): void;
    nodeChanged(node: DzNode): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzNumericProperty {
    clearMap(): void;
    copyMapFrom(otherProp: DzNumericProperty): void;
    doesClampChangeValue(): boolean;
    findMatchingProperty(node: DzNode, useStrictMatching: boolean): DzProperty;
    getDefaultMapGamma(): number;
    getDefaultMapTextureType(): number;
    getDoubleDefaultValue(): number;
    getDoubleValue(tm: number): number;
    getDoubleValue(): number;
    getFollowProperty(): DzNumericProperty;
    getFollowValue(): number;
    getFollowValue(tm: number): number;
    getLinkProperty(): DzNumericProperty;
    getMapValue(): DzTexture;
    getMapValue(time: number): DzTexture;
    getNDoubleValue(): any[];
    getNDoubleValue(tm: number): any[];
    getNValueCount(): number;
    getTextureModifier(): DzTextureModifier;
    getTextureModifierFlags(): number;
    getValueAsFloatColor(tm: number): DzFloatColor;
    getValueAsFloatColor(): DzFloatColor;
    getValueAsInt2(): DzInt2;
    getValueAsInt2(tm: number): DzInt2;
    getValueAsVec2(): DzVec2;
    getValueAsVec2(tm: number): DzVec2;
    getValueAsVec3(): DzVec3;
    getValueAsVec3(tm: number): DzVec3;
    getXYZInterest(): XYZInterest;
    insertController(controller: DzNumericController, idx: number): void;
    isClamped(): boolean;
    isInvalidWithoutMap(): boolean;
    isLinked(): boolean;
    isMappable(): boolean;
    isMapped(): boolean;
    isMaster(): boolean;
    isModulo(): boolean;
    linkTo(master: DzNumericProperty): void;
    setDefaultMapGamma(gamma: number): void;
    setDefaultMapTextureType(type: number): void;
    setDoubleDefaultValue(val: number): void;
    setDoubleValue(val: number): void;
    setDoubleValue(tm: number, val: number): void;
    setIsClamped(val: boolean): void;
    setIsMappable(val: boolean): void;
    setIsModulo(val: boolean): void;
    setMap(imgFile: string): void;
    setMap(img: DzTexture): void;
    setMustHaveMap(val: boolean): void;
    setTextureModifier(txtMod: DzTextureModifier): void;
    setTextureModifierFlags(flags: number): void;
    setXYZInterest(interest: XYZInterest): void;
    unlink(): void;

    // SIGNALS
    clampedChanged(onOff: boolean): void;
    defaultMapGammaChanged(): void;
    defaultMapTextureTypeChanged(): void;
    isMappableChanged(): void;
    linked(): void;
    mapChanged(): void;
    minMaxChanged(): void;
    textureModifierChanged(): void;
    textureModifierFlagsChanged(): void;
    unlinked(): void;
}

/**
 * Example:
 */
declare class Object {
    constructor(): Function;
    prototype: any;
    __proto__: any;

    create(obj: any, properties: any): any;
    defineProperties(obj: any, properties: any): any;
    defineProperty(obj: any, property: string, descriptor: any): any;
    getOwnPropertyDescriptor(obj: any, property: string): any;
    getOwnPropertyNames(obj: any): any[];
    getPrototypeOf(obj: any): any;
    keys(obj: any): any[];
    hasOwnProperty(property: string): boolean;
    isPrototypeOf(obj: any): boolean;
    propertyIsEnumerable(property: string): boolean;
    toLocaleString(): string;
    toString(): string;
    valueOf(): any;
    __defineGetter__(propertyName: string, getter: Function): void;
    __defineSetter__(propertyName: string, setter: Function): void;
}

/**
 * Responsible for evaluating the geometry pipeline, including caching and drawing of the world-space transformed shape. Can have multiple shapes assigned, though only one can be active at a time.
 */
declare class DzObject {
    addModifier(modifier: DzModifier, index: number): DzError;
    addShape(shape: DzShape, index: number): DzError;
    findModifier(name: string): DzModifier;
    findModifierIndex(mod: DzModifier): number;
    findModifierIndexFromEnd(mod: DzModifier): number;
    forceCacheUpdate(node: DzNode, isRender: boolean): void;
    getBoundingBox(): DzBox3;
    getCachedGeom(): DzVertexMesh;
    getCurrentShape(): DzShape;
    getGeometryControl(): DzEnumProperty;
    getLocalBoundingBox(): DzBox3;
    getLocalOrientedBox(): DzOrientedBox3;
    getModifier(which: number): DzModifier;
    getNumModifiers(): number;
    getNumShapes(): number;
    getShape(which: number): DzShape;
    invalidateCache(): void;
    isBuildingGeom(): boolean;
    isBuildingGeomValid(): boolean;
    moveModifier(modifier: DzModifier, index: number): DzError;
    moveShape(shape: DzShape, index: number): DzError;
    removeAllModifiers(): DzError;
    removeAllShapes(): DzError;
    removeModifier(modifier: DzModifier): DzError;
    removeShape(index: number): DzError;

    // SIGNALS
    aboutToAddModifier(mod: DzModifier): void;
    aboutToDelete(): void;
    aboutToFinalize(mesh: DzVertexMesh): void;
    cachedGeomFinalized(): void;
    cachedGeomInvalidated(): void;
    cachedGeomUpdated(): void;
    cachedTopologyChanged(): void;
    currentShapeSwitched(): void;
    drawnDataChanged(): void;
    materialListChanged(): void;
    materialSelectionChanged(): void;
    materialSelectionSetsChanged(): void;
    modifierAdded(mod: DzModifier): void;
    modifierRemoved(mod: DzModifier): void;
    modifierStackChanged(): void;
    shapeAdded(shape: DzShape): void;
    shapeRemoved(shape: DzShape): void;
    shapeTopologyChanged(): void;
    uvsChanged(): void;
}

/**
 * This page exists in order to indicate the script accessible portions of QObject . QObject is the base type of all objects in the Daz Studio API . See Also: Object
 */
declare class QObject {
    objectName(): string;
    name: string;

    deleteLater(): void;
    toString(): string;
    className(): string;
    inherits(classname: string): boolean;

    // SIGNALS
    destroyed(obj: QObject): void;
}

/**
 * A specialization of DzExporter that implements an exporter for the Wavefront Object (.obj) format. See Also: DzExportMgr :: findExporterByClassName () DzExportMgr :: findExporter () Sample: Silent OBJ Export
 */
declare class DzObjExporter {
}

/**
 * See Also: DzImportMgr :: findImporterByClassName () DzImportMgr :: findImporter () Sample: Silent OBJ Import
 */
declare class DzObjImporter {
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureComponent instead.
 */
declare class DzOffsetManip {
    xOffset(): number;
    yOffset: number;

    setOffset(x: number, y: number): void;
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureComponent instead.
 */
declare class DzOpacityManip {
    opacity(): number;

    getOpacity(): number;
    setOpacity(opacity: number): void;
}

/**
 * You can access the global instance of DzOpenGL via the Global :: OpenGL variable.
 */
declare class DzOpenGL {
    isOGLInitialized(): boolean;
    getBoundingBoxActiveOpacity(): number;
    getBoundingBoxEdgeLength(): number;
    getBoundingBoxInactiveOpacity(): number;
    getDepthBufferBits(): number;
    getDrawNodeHighlight(): boolean;
    getMajorVersion(): number;
    getMaxTextureSize(): number;
    getMaxTextureUnits(): number;
    getMinorVersion(): number;
    getNumAuxBuffers(): number;
    getNumLights(): number;
    getNumOGLExtensions(): number;
    getOpenGLVersion(): number;
    getPBuffer(): pbuffer_dz;
    getReleaseNumber(): number;
    getSubDivisionWireOpacity(): number;
    getTextureQuality(): OGLTexQuality;
    getTextureQualityMaxSize(): number;
    getTriDivisionWireOpacity(): number;
    getWireframeOpacity(): number;
    isDisplayOptimizationEnabled(): boolean;
    isMultisampleEnabled(): boolean;
    isMultisampleSupported(): boolean;
    isOGLExtensionSupported(extension: string): boolean;
    isOGLShaderLanguageSupported(): boolean;
    isShadowingSupported(): boolean;
    isVBOSupported(): boolean;
    setBoundingBoxActiveOpacity(opacity: number): void;
    setBoundingBoxEdgeLength(length: number): void;
    setBoundingBoxInactiveOpacity(opacity: number): void;
    setDisplayOptimizationEnabled(onOff: boolean): void;
    setDrawNodeHighlight(onOff: boolean): void;
    setMultisampleEnabled(onOff: boolean): void;
    setSubDivisionWireOpacity(opacity: number): void;
    setTextureQuality(quality: OGLTexQuality): void;
    setTriDivisionWireOpacity(opacity: number): void;
    setWireframeOpacity(opacity: number): void;

    // SIGNALS
    boundingBoxActiveOpacityChanged(value: number): void;
    boundingBoxEdgeLengthChanged(value: number): void;
    boundingBoxInactiveOpacityChanged(value: number): void;
    displayOptimizationEnabled(onOff: boolean): void;
    multisampleEnabled(onOff: boolean): void;
    subDivisionWireOpacityChanged(value: number): void;
    subWireframeOpacityChanged(value: number): void;
    textureQualityChanged(quality: OGLTexQuality): void;
}

/**
 * Represents a 3D box by storing two 3D vectors - an upper and lower corner for the box, and a transformation for its orientation.
 */
declare class DzOrientedBox3 {
    localBox(): DzBox3;
    transform: DzMatrix3;

    toString(): string;
}

/**
 * This is the script counterpart to the QPalette type used in the C++ SDK. Attention: Inheritance will change to Object in a pending update.
 */
declare class Palette {
    active(): Palette;
    alternateBase: { r: number, g: number, b: number, a: number };
    background: { r: number, g: number, b: number, a: number };
    base: { r: number, g: number, b: number, a: number };
    brightText: { r: number, g: number, b: number, a: number };
    button: { r: number, g: number, b: number, a: number };
    buttonText: { r: number, g: number, b: number, a: number };
    dark: { r: number, g: number, b: number, a: number };
    disabled: Palette;
    foreground: { r: number, g: number, b: number, a: number };
    highlight: { r: number, g: number, b: number, a: number };
    highlightedText: { r: number, g: number, b: number, a: number };
    inactive: Palette;
    light: { r: number, g: number, b: number, a: number };
    link: { r: number, g: number, b: number, a: number };
    linkVisited: { r: number, g: number, b: number, a: number };
    mid: { r: number, g: number, b: number, a: number };
    midlight: { r: number, g: number, b: number, a: number };
    shadow: { r: number, g: number, b: number, a: number };
    text: { r: number, g: number, b: number, a: number };
    toolTipBase: { r: number, g: number, b: number, a: number };
    toolTipText: { r: number, g: number, b: number, a: number };
    window: { r: number, g: number, b: number, a: number };
    windowText: { r: number, g: number, b: number, a: number };
}

/**
 * A “Pane” is the application's implementation of a persistent non-modal set of closely related widgets that can be stacked, ordered, docked, undocked, minimized, restored, shown, hidden, positioned and/or resized by the end-user. Each pane has a label that is attached to the outer perimeter of the pane; whether the label appears as a tab/button/etc. to the user depends on the “style” that they currently has applied. A pane's label should briefly describe the concept (product, service, etc.) presented to the user within the pane. Actions performed by the user that are closely related to the concept of a given pane, but do not warrant a persistent widget within the pane itself, or are more advanced in nature, should be considered for placement with the pane's option menu. A pane is only ever displayed to the user within a DzPaneGroup ; this is what gives the pane its ability to be stacked, ordered, docked, undocked, minimized, restored, shown, hidden, positioned and/or resized. A pane can only ever exist within one DzPaneGroup at a time. Panes are singletons; there is only one instance of a given DzPane subclass. Panes are registered with DzPaneMgr and are available to access and modify via script. Use DzPaneMgr :: findPane () to obtain a pointer to the single instance of the subclass, using its classname.
 */
declare class DzPane {
    buildOptionsMenu(menu: DzActionMenu): void;
    getLabel(): string;
    getOptionsMenu(): DzActionMenu;
    getOptionsMenuVersion(): number;
    getPaneGroup(): DzPaneGroup;
    hidePane(): void;
    moveToGroup(group: DzPaneGroup): void;
    refresh(): void;
    restoreSettings(settings: DzPaneSettings): void;
    saveSettings(settings: DzPaneSettings): void;
    setLabel(label: string): void;
    showPane(): void;
    undock(pos: Point, size: Size): void;
    undockGroup(pos: Point, size: Size): void;
    makeGroupUndockable(): void;
    makeUndockable(minSize: Size): void;
    makeGroupDockable(): void;

    // SIGNALS
    labelChanged(newLabel: string): void;
    menuChanged(): void;
    paneGroupChanged(oldGroup: DzPaneGroup, newGroup: DzPaneGroup): void;
    tabBarHiddenChanged(hidden: boolean): void;
    visibilityChanged(onOff: boolean): void;
}

/**
 * DzPaneAction subclasses are automatically added to the main menu under 'Window > Panes (Tabs)'.
 */
declare class DzPaneAction {
    getPaneIdentifier(): string;
}

/**
 * A Pane Group serves as a collection of container widgets ( DzPane ) that are themselves used to organize discrete portions of the interface. A pane group is exposed at the top-level of the user interface and is used to stack DzPane instances within the same area. A pane group can be docked (“anchored”) within a DzDockArea or undocked (“detached”) and made to float above the rest of the interface. A pane group provides an easy-to-use selection mechanism (i.e., a tab bar) for choosing which DzPane instance in the stack to display to the user. When a pane group contains more DzPane instances than can be sufficiently represented within the tab bar, additional scrolling controls are presented to the user.
 */
declare class DzPaneGroup {
    fitScreen(): void;
    fitScreenHeight(): void;
    fitScreenWidth(): void;
    getCurrentPane(): DzPane;
    getDragOffset(): Point;
    getNumPanes(): number;
    getNumShownPanes(): number;
    getPane(index: number): DzPane;
    hideAllPanes(): void;
    hidePane(pane: DzPane): void;
    hideTabBar(yesNo: boolean): void;
    setPaneEnabled(pane: DzPane, enabled: boolean): void;
    setUndockedTabBarPosition(pos: TabBarPosition): void;
    showPane(pane: DzPane): void;
    tabBarHidden(): boolean;
    undockedTabBarPosition(): TabBarPosition;
    updateTabPosition(): void;
    isUndockable(): boolean;

    // SIGNALS
    emptyGroup(): void;
}

/**
 * This class manages layouts, activity layouts, pane groups, panes, and toolbars. There is only one instance of this manager in an application. This instance is created and owned by DzMainWindow . Request the instance via DzMainWindow :: getPaneMgr (). See Also: Global :: MainWindow DzActivityLayout DzPane DzPaneGroup DzToolBar
 */
declare class DzPaneMgr {
    addActivityLayout(layout: DzActivityLayout): void;
    clearAllGroups(): void;
    createActivityLayout(name: string, description: string): DzActivityLayout;
    createEmptyPaneGroup(): DzPaneGroup;
    createToolBar(name: string): DzToolBar;
    enableActivityBar(onOff: boolean): void;
    findActivityLayout(name: string): DzActivityLayout;
    findDockBar(className: string): DzDockBar;
    findDockBarByName(name: string): DzDockBar;
    findPane(identifier: string): DzPane;
    findToolBar(name: string): DzToolBar;
    getActiveActivityLayout(): DzActivityLayout;
    getActiveActivityLayoutIndex(): number;
    getActivityBarImage(): string;
    getActivityBarImageList(): any[];
    getActivityLayout(i: number): DzActivityLayout;
    getActivityLayoutList(): any[];
    getAdvancedLayout(): string;
    getBasicLayout(): string;
    getDefaultLayout(): string;
    getDefaultLayoutNames(): any[];
    getDockBar(i: number): DzDockBar;
    getDockBarList(): any[];
    getNumActivityLayouts(): number;
    getNumDockBars(): number;
    getNumPaneGroups(): number;
    getNumPanes(): number;
    getNumToolBars(): number;
    getOrientTabsAlongTop(): boolean;
    getPane(i: number): DzPane;
    getPaneGroup(i: number): DzPaneGroup;
    getPaneGroupList(): any[];
    getPaneList(): any[];
    getProLayout(): string;
    getSessionLayout(): string;
    getShowLessonStrip(): boolean;
    getSimpleLayout(): string;
    getStandardLayout(): string;
    getToolBar(i: number): DzToolBar;
    getToolBarList(): any[];
    getUseWorkflowAssistance(): boolean;
    hideAllPanes(): void;
    hideAllToolBars(): void;
    hidePane(identifier: string): DzError;
    hidePane(pane: DzPane): DzError;
    hidePaneGroup(group: DzPaneGroup): DzError;
    hidePaneGroup(i: number): DzError;
    isActivityBarEnabled(): boolean;
    loadNextActivityBarImage(): void;
    movePaneGroup(group: DzPaneGroup, dock: DockSide): DzError;
    movePaneGroup(group: DzPaneGroup, dock: DockSide, index: number, newLine: boolean): DzError;
    removeActivityLayout(name: string): boolean;
    removeActivityLayout(i: number): boolean;
    removeAllActivityLayouts(): void;
    removeAllToolBars(): void;
    removePaneGroup(group: DzPaneGroup): void;
    removeToolBar(name: string): void;
    restoreLayout(filename: string, executeScript: boolean): DzError;
    saveLayout(filename: string, description: string): DzError;
    selectLesson(path: string): boolean;
    setActiveActivityLayout(layout: DzActivityLayout): void;
    setActiveActivityLayout(i: number): void;
    setActivityBarImage(img: string): void;
    setOrientTabsAlongTop(onOff: boolean): void;
    setPaneEnabled(identifier: string, enabled: boolean): DzError;
    setPaneEnabled(pane: DzPane, enabled: boolean): DzError;
    setSessionLayout(filename: string): DzError;
    setShowLessonStrip(onOff: boolean): void;
    setUseWorkflowAssistance(onOff: boolean): void;
    showAllPanes(): void;
    showPane(pane: DzPane): DzError;
    showPane(identifier: string): DzError;
    showPaneGroup(group: DzPaneGroup): DzError;
    showPaneGroup(i: number): DzError;
    tearOffPane(index: number, x: number, y: number): DzError;
    tearOffPane(identifier: string, x: number, y: number): DzError;
    tearOffPane(pane: DzPane, x: number, y: number): DzError;
    togglePane(pane: DzPane): DzError;
    togglePane(identifier: string): DzError;
    togglePane(index: number): DzError;
    getNumPaneGroupDlgs(): number;
    getPaneGroupDlg(i: number): DzPaneGroupDlg;
    addPaneGroupDlg(dlg: DzPaneGroupDlg): void;
    removePaneGroupDlg(dlg: DzPaneGroupDlg): void;
    closeAllPaneGroupDlgs(): void;

    // SIGNALS
    activeLayoutAboutToChange(newLayoutIdx: number): void;
    activeLayoutChanged(i: number): void;
    activityBarEnabled(onOff: boolean): void;
    layoutListChanged(): void;
    layoutRestored(filename: string): void;
    orientTabsAlongTopChanged(onOff: boolean): void;
    toolbarListChanged(): void;
    workflowAssistanceEnableStateChanged(onOff: boolean): void;
    workflowAssistanceModeChanged(): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzPaneSettings {
}

/**
 * This container type does not directly support assets. The primary purpose of this container type is to serve as a parent for collating products that bear the same first significant character in their respective titles. This container type is most notably used for navigation in the “Content Library” pane.
 */
declare class DzParentProductContainer {
    updateChildren(): boolean;
}

/**
 * A DzPathComboBox provides a DzComboBox like widget with a popup that is designed for choosing a path.
 */
declare class DzPathComboBox {
    clearSelection(): void;
    currentType(): DzTypeAssetContainer;
    currentType(): string;
    getRoot(): DzTypeAssetContainer;
    getSelectionPath(): any[];
    setEmptyText(text: string): void;
    setSelection(idPath: any[]): void;
    setTopLevelType(idPath: any[]): void;
    setTypes(list: any[]): void;

    // SIGNALS
    pathSelectionChanged(path: string): void;
    viewAboutToShow(): void;
}

/**
 * Persistent menus are registered with the DzActionMgr singleton and are available to access and modify via script.
 */
declare class DzPersistentMenu {
    clearActiveWgt(): void;
    getActionMenu(): DzActionMenu;
    getActiveWgt(): QWidget;
    setActiveWgt(wgt: QWidget): void;
}

/**
 * This view tool provides the user with the ability to select items displayed in a Dz3DViewport by simply clicking on it.
 */
declare class DzPickTool {
    getNodeClickMode(): NodeClickMode;
    lineWidth(): number;
    setLineWidth(width: number): void;

    // SIGNALS
    changedLineWidth(width: number): void;
}

/**
 * This is the script counterpart to the QPixmap type used in the C++ SDK. Attention: Inheritance will change to Object in a pending update.
 */
declare class Pixmap {
    depth(): number;
    height: number;
    rect: Rect;
    size: Size;
    width: number;

    fill(color: { r: number, g: number, b: number, a: number }): void;
    fromImage(image: Image): void;
    isNull(): boolean;
    load(filename: string, format: string): boolean;
    loadFromData(data: ByteArray, format: string): boolean;
    resize(width: number, height: number): void;
    resize(size: Size): void;
    save(filename: string): void;
    toImage(): Image;
}

/**
 * This class provides startup and shutdown functionality for DAZ Studio plug-ins and maintains the list of class types exported by the plug-in.
 */
declare class DzPlugin {
    getAuthor(): string;
    getDescription(): string;
    getEvaluationInformation(): string;
    getFilename(): string;
    getLoadOnStart(): boolean;
    getName(): string;
    getPrefixes(): any[];
    getStatus(): Status;
    getStatusInformation(): string;
    getStatusString(): string;
    getVersion(): DzVersion;
    getVersionString(): string;
    isActivated(): boolean;
    isRegistered(): boolean;
    validateSerialNumber(serialNumber: string, saveIfValid: boolean): boolean;
}

/**
 * Responsible for the management of dynamically loaded libraries (aka “plugins”) that extend the features/functionality of the core application. There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getPluginMgr (). See Also: Global :: App Sample: Plugins Load Config
 */
declare class DzPluginMgr {
    doAboutPluginsDlg(): void;
    findPlugin(pluginName: string): DzPlugin;
    getNumPlugins(): number;
    getPlugin(which: number): DzPlugin;
    promptRestartRequired(): void;
    saveConfiguration(): boolean;
    setPluginLoadOnStartup(plugin: DzPlugin, onOff: boolean): void;

    // SIGNALS
    pluginAdded(plugin: DzPlugin): void;
}

/**
 * This is the script counterpart to the QPoint type used in the C++ SDK. A Point object is a two dimensional representation of a x (horizontal) and y (vertical) position. Attention: Inheritance will change to Object in a pending update.
 */
declare class Point {
    x(): number;
    y: number;

    cursorPos(): Point;
}

/**
 * TODO: Add detailed description.
 */
declare class DzPointLight {
    getDecay(): number;
    getDecayControl(): DzFloatProperty;
    getDisplayPersistence(): boolean;
    getDisplayPersistenceControl(): DzBoolProperty;
    getFalloffDistance(lightPercent: number): number;
    getLightProfile(): string;
    getLightProfileControl(): DzFileProperty;
    getLightVisibility(): boolean;
    getSphereOpacity(): number;
    getSphereOpacityControl(): DzFloatProperty;
    setDecay(decay: number): void;
    setDisplayPersistence(persistence: boolean): void;
    setLightProfile(profilePath: string): void;
    setSphereOpacity(opacity: number): void;
}

/**
 * Provides a menu widget for use in context menus and other popup menus. A menu consists of a list of items. There are three kinds of items: separators, items that show a submenu, and items that perform an action. Submenu items and action items have an identifier (id) and a position (index). Separators have a position (index) and a common identifier (-1). Separators are inserted with insertSeparator (). Submenus are inserted with insertSubmenuItem (), insertTextSubmenuItem (), or insertPixmapSubmenuItem (). All other items are considered action items, and are inserted with insertItem (), insertTextItem () or insertPixmapItem (). Submenu items and action items can have text, a pixmap, or both. Clearing an entire menu is accomplished with clear () and removing individual items is accomplished with removeItem () or removeItemAt (). To make a menu visible on the screen, use exec () or popup () - do not use show ().
 */
declare class DzPopupMenu {
    checkable(): boolean;
    tearOff: boolean;

    clear(): void;
    connectItem(id: number, receiver: any, member: string): boolean;
    connectItem(id: number, thisObject: any, functionRef: Function): boolean;
    disconnectItem(id: number, receiver: any, member: string): boolean;
    disconnectItem(id: number, thisObject: any, functionRef: Function): boolean;
    exec(): number;
    exec(pos: Point, indexAtPoint: number): number;
    idAt(index: number): number;
    idAt(pos: Point): number;
    insertItem(pixmap: Pixmap, text: string, id: number, index: number): number;
    insertPixmapItem(pixmap: Pixmap, id: number, index: number): number;
    insertPixmapSubmenuItem(pixmap: Pixmap, popup: DzPopupMenu, id: number, index: number): number;
    insertSeparator(index: number): number;
    insertSubmenuItem(pixmap: Pixmap, text: string, popup: DzPopupMenu, id: number, index: number): number;
    insertTextItem(text: string, id: number, index: number): number;
    insertTextSubmenuItem(text: string, popup: DzPopupMenu, id: number, index: number): number;
    isItemCheckable(id: number): boolean;
    isItemChecked(id: number): boolean;
    isItemEnabled(id: number): boolean;
    isItemVisible(id: number): boolean;
    itemParameter(id: number): number;
    numItems(): number;
    pixmap(id: number): Pixmap;
    popup(pos: Point, indexAtPoint: number): void;
    removeItem(id: number): void;
    removeItemAt(index: number): void;
    setActiveItem(id: number): void;
    setItemCheckable(id: number, yesNo: boolean): void;
    setItemChecked(id: number, yesNo: boolean): void;
    setItemEnabled(id: number, yesNo: boolean): void;
    setItemParameter(id: number, param: number): boolean;
    setItemVisible(id: number, yesNo: boolean): void;
    setPixmap(id: number, pixmap: Pixmap): void;
    setText(id: number, text: string): void;
    setWhatsThis(id: number, text: string): void;
    text(id: number): string;
    whatsThis(id: number): string;
    insertTearOffHandle(): number;
    insertItem(text: string, id: number, index: number): number;
    insertItem(pixmap: Pixmap, id: number, index: number): number;
    insertItem(text: string, popup: DzPopupMenu, id: number, index: number): number;
    insertItem(pixmap: Pixmap, popup: DzPopupMenu, id: number, index: number): number;
    changeItem(id: number, text: string): void;
    changeItem(id: number, pixmap: Pixmap): void;
    updateItem(id: number): void;

    // SIGNALS
    aboutToHide(): void;
    aboutToShow(): void;
    activated(id: number): void;
    highlighted(id: number): void;
}

/**
 * An asset save filter for saving a Pose Preset in the DSON format. See Also: Sample: Save a Pose Preset
 */
declare class DzPoseAssetFilter {
}

/**
 * The name of this data item is “PoserIKTarget”.
 */
declare class DzPoserIKTargetFlag {
}

/**
 * The name of this data item is “PoserNonPropagatingScaleFlag”.
 */
declare class DzPoserNonPropagatingScaleFlag {
}

/**
 * The name of this data item is “PoserPropagatingScaleFlag”.
 */
declare class DzPoserPropagatingScaleFlag {
}

/**
 * See Also: DzProperty
 */
declare class DzPresentation {
    autoFitBase(): string;
    colorA: { r: number, g: number, b: number, a: number };
    colorB: { r: number, g: number, b: number, a: number };
    description: string;
    extendedBases: any[];
    iconLarge: string;
    iconSmall: string;
    label: string;
    preferredBase: string;
    type: string;
}

/**
 * See Also: Sample: Render To RIB (line #440+)
 */
declare class DzProcess {
    arguments(): any[];
    communication: Communication;
    exitStatus: number;
    normalExit: boolean;
    running: boolean;
    workingDirectory: string;

    canReadLineStderr(): boolean;
    canReadLineStdout(): boolean;
    closeStdin(): void;
    kill(): void;
    launch(buffer: string, env: any[]): boolean;
    readLineStderr(): string;
    readLineStdout(): string;
    readStderr(): string;
    readStdout(): string;
    start(env: any[]): boolean;
    tryTerminate(): void;
    writeToStdin(buffer: string): void;

    // SIGNALS
    launchFinished(): void;
    processExited(): void;
    readyReadStderr(): void;
    readyReadStdout(): void;
    wroteToStdin(): void;
}

/**
 * The “Product” container type represents a collection of assets (and supporting files/metadata) that are presented as a single entity to the end-user. Each product is assigned a Globally Unique Identifier (GUID) that is used to identify that entity within the content ecosystem. Once a GUID has been assigned to a product (at creation), it does not (and should not) change. While nearly all of the information that defines a product can be replicated into another, for logistical reasons a GUID can only be associated with one “Store” (source) at any single moment in its lifetime. This means that if more than one content package containing metadata that defines a given GUID is installed by an end-user, the last package installed will define the product in the database. By default, all newly created assets are assigned to a “LOCAL USER” product. This product is represented by a GUID consisting entirely of zeros; i.e., “00000000-0000-0000-0000-000000000000” The “LOCAL USER” product is associated with the “LOCAL USER” store (source); this cannot be modified. See Also: DzAssetMgr :: findProductByGuid () DzAssetMgr :: findProductByStoreToken () DzAssetMgr :: createProduct () DzAssetMgr :: createProductFromContainer () DzAssetMgr :: createProductFromAssets () DzAssetMgr :: createStore () DzAsset
 */
declare class DzProductAssetContainer {
    artistNames(): any[];
    dateInstalled: Date;
    dateLastUpdated: Date;
    datePurchased: Date;
    dateReleased: Date;
    description: string;
    groupId: number;
    guid: string;
    hasCloudMetadata: boolean;
    hidden: boolean;
    iconPath: string;
    isCloudInstallable: boolean;
    isCloudInstalled: boolean;
    isCloudOperationInProgress: boolean;
    isCloudOwned: boolean;
    isDownloadingFromCloud: boolean;
    isInstalled: boolean;
    isLocalUser: boolean;
    isLocalUserStore: boolean;
    isMetadataValid: boolean;
    isVendor: boolean;
    needsCloudInstall: boolean;
    needsCloudUpdate: boolean;
    store: string;
    storeID: number;
    title: string;
    token: string;
    url: string;

    getDefaultStoreIconSize(): Size;
    cancelFromCloud(): void;
    clearGroup(): void;
    getCategories(metaType: ProductMetadataType, installedAssets: boolean): any[];
    getIconSize(): Size;
    getImage(): Image;
    getMetadataXML(metaType: ProductMetadataType): string;
    getMetadataXMLPath(userData: boolean): string;
    getRelativeInstallPath(): string;
    getSupportFiles(forceRefresh: boolean): any[];
    getURL(): string;
    installFromCloud(): void;
    isGroup(group: number): boolean;
    loadDefaultIcon(): boolean;
    loadProductImage(): boolean;
    pushMetadata(): boolean;
    remove(notify: boolean): boolean;
    setIconSize(size: Size): void;
    setImage(img: Image): void;
    setURL(url: string): void;
    uninstall(): void;
    uninstallFromCloud(): void;
    updateFromCloud(): void;
    updateMetaDataFromCloud(force: boolean): void;
}

/**
 * This container type does not directly support assets. The primary purpose of this container type is to collect results returned by a database query for products. See Also: DzAssetMgr :: searchForProducts ()
 */
declare class DzProductHolderContainer {
    insertChildProductContainer(container: DzProductAssetContainer): boolean;
}

/**
 * An asset save filter for saving a Properties Preset in the DSON format. See Also: Sample: Save a Properties Preset
 */
declare class DzPropertiesAssetFilter {
}

/**
 * This is the base class for all properties that are owned or controlled by Elements. Properties can be keyable or not. See Also: DzElement
 */
declare class DzProperty {
    assetAuthor(): DzAuthor;
    assetFileRevision: DzVersion;
    assetId: string;
    assetModifiedDate: Date;
    assetNeedSave: boolean;
    assetSource: DzUri;
    assetUri: DzUri;
    emitValueChangedOnSceneClear: boolean;

    addValueToSettings(tm: number, settings: DzSettings, flags: PropertyValueSettingsFlags): void;
    addValueToSettings(settings: DzSettings, flags: PropertyValueSettingsFlags): void;
    beginEdit(): void;
    buildIdUriToRoot(rootNode: DzNode): DzUri;
    buildNameUriToRoot(rootNode: DzNode): DzUri;
    canAnimate(): boolean;
    canAutoFollow(): boolean;
    cancelEdit(): void;
    clearRegion(preservePath: boolean): void;
    copyFrom(prop: DzProperty): void;
    copyToClipboard(): propertyclipboard_dz;
    createAlias(): DzProperty;
    currentValueIsDefaultValue(): boolean;
    currentValueIsDefinitionValue(): boolean;
    deleteAllKeys(): void;
    deleteKeys(start: number, end: number): number;
    deleteKeys(interval: DzTimeRange): number;
    deleteSelectedKeys(): number;
    doCurrentAttributesMatchDefinition(): boolean;
    findKeyIndex(tm: number): number;
    findMatchingProperty(node: DzNode): DzProperty;
    finishEdit(): void;
    getAlias(index: number): DzProperty;
    getAliasTarget(): DzProperty;
    getAttributes(settings: DzPropertySettings): void;
    getAutoFollowTargetUri(): DzUri;
    getController(idx: number): DzController;
    getControllerList(): any[];
    getGroup(): DzPropertyGroup;
    getIndexOfSlaveControllers(controller: DzController): number;
    getKeyInterpolationType(i: number): InterpolationType;
    getKeyInterpolationTypeValues(i: number): any[];
    getKeyRange(): DzTimeRange;
    getKeyTime(i: number): number;
    getLabel(): string;
    getNumAliases(): number;
    getNumControllers(): number;
    getNumKeys(): number;
    getNumKeys(range: DzTimeRange): number;
    getNumSelectedKeys(): number;
    getNumSlaveControllers(): number;
    getOwner(): DzElement;
    getPath(): string;
    getPresentation(): DzPresentation;
    getRegion(): geometryregion_dz;
    getSelectedKeyRange(): DzTimeRange;
    getSlaveController(idx: number): DzController;
    getSlaveControllerList(): any[];
    getWidgetClass(styled: boolean): string;
    getWidgetClassOverride(styled: boolean): string;
    hasControllers(): boolean;
    hasKeys(): boolean;
    hasSlaveControllers(): boolean;
    hasWidgetClassOverride(styled: boolean): boolean;
    isAlias(): boolean;
    isCombinable(prop: DzProperty): boolean;
    isDynamicallyAutoFollow(): boolean;
    isDynamicallyHidden(): boolean;
    isEditing(): boolean;
    isFavorite(): boolean;
    isGlobalFavorite(): boolean;
    isHidden(): boolean;
    isKeySelected(i: number): boolean;
    isLocked(): boolean;
    isManipulator(): boolean;
    isNew(): boolean;
    isNumeric(): boolean;
    isOverridingControllers(): boolean;
    isPrivateProperty(): boolean;
    isRigProperty(): boolean;
    isSelected(): boolean;
    isUserProperty(): boolean;
    lock(onOff: boolean): void;
    modifyAsset(newUri: DzUri): boolean;
    modifyAsset(): boolean;
    moveControllerToIndex(controller: DzController, newIdx: number): boolean;
    moveControllerToIndex(curIdx: number, newIdx: number): boolean;
    propertyDuplicate(): DzProperty;
    rawValueIsDefinitionValue(): boolean;
    removeAllControllers(): void;
    removeController(prop: DzProperty): void;
    removeController(idx: number): void;
    removeController(controller: DzController): void;
    reset(resetFlags: PropertyResetFlags): void;
    restoreAttributesFromDefinition(): void;
    selectAllKeys(onOff: boolean): number;
    selectKey(i: number, onOff: boolean): void;
    selectKeys(range: DzTimeRange, onOff: boolean): number;
    setAttributes(settings: DzPropertySettings): void;
    setAutoFollowTargetUri(path: DzUri): void;
    setCanAnimate(yesNo: boolean): void;
    setCanAutoFollow(onOff: boolean): void;
    setDynamicallyAutoFollow(yesNo: boolean): void;
    setDynamicallyHidden(yesNo: boolean): void;
    setHidden(yesNo: boolean): void;
    setIsFavorite(onOff: boolean): void;
    setIsGlobalFavorite(onOff: boolean): void;
    setIsManipulator(onOff: boolean): void;
    setIsRigProperty(yesNo: boolean): void;
    setIsUserProperty(yesNo: boolean): void;
    setKeyInterpolationType(i: number, interp: InterpolationType, param0: number, param1: number, param2: number): void;
    setKeyInterpolationType(i: number, interp: InterpolationType): void;
    setLabel(label: string): void;
    setNew(onOff: boolean): void;
    setOverrideControllers(onOff: boolean): void;
    setPath(path: string): void;
    setPresentation(pres: DzPresentation): void;
    setRegion(reg: geometryregion_dz): void;
    setSelected(onOff: boolean): void;
    setValueFromSettings(settings: DzSettings, flags: PropertyValueSettingsFlags): void;
    setValueFromSettings(tm: number, settings: DzSettings, flags: PropertyValueSettingsFlags): void;
    setWidgetClassOverride(styledWgtClassName: string, wgtClassName: string): DzError;

    // SIGNALS
    aliasListChanged(): void;
    assetModified(): void;
    assetWasSaved(): void;
    autoFollowTargetUriChanged(path: DzUri): void;
    canAnimateChanged(enabled: boolean): void;
    canAutoFollowChanged(canAutoFollow: boolean): void;
    controllerListChanged(): void;
    currentValueChanged(): void;
    dynamicallyAutoFollowChanged(onOff: boolean): void;
    dynamicallyHiddenChanged(hidden: boolean): void;
    editFinished(): void;
    groupChanged(group: DzPropertyGroup): void;
    hiddenChanged(hidden: boolean): void;
    isFavoriteChanged(onOff: boolean): void;
    isGlobalFavoriteChanged(onOff: boolean): void;
    isManipulatorChanged(isManip: boolean): void;
    isUserPropertyChanged(isUserProp: boolean): void;
    keySelectionChanged(range: DzTimeRange): void;
    labelChanged(newLabel: string): void;
    lockStateChanged(): void;
    newStateChanged(): void;
    overridingControllersChanged(overriding: boolean): void;
    presentationIconChanged(): void;
    propertyDeleted(prop: DzProperty): void;
    regionChanged(): void;
    removed(): void;
    selectionStateChanged(): void;
    slaveControllerListChanged(): void;
    valueChanged(range: DzTimeRange): void;
}

/**
 * DzPropertyGroup objects are all owned and managed by DzElement objects. Do not create property groups yourself - they are automatically created as needed when you assign individual properties to a group. To iterate through the property groups for an element, use DzElement :: getPropertyGroups () to get the property group tree that the element's properties are grouped in. See Also: DzPropertyGroupTree
 */
declare class DzPropertyGroup {
    getDefaultGroupName(): string;
    findChild(name: string): DzPropertyGroup;
    findProperty(propName: string, traverse: boolean, recurse: boolean): DzProperty;
    findPropertyByLabel(propLabel: string, traverse: boolean, recurse: boolean): DzProperty;
    findSibling(name: string): DzPropertyGroup;
    getAllPaths(): any[];
    getAllProperties(): any[];
    getCollapsed(): boolean;
    getFirstChild(): DzPropertyGroup;
    getNextSibling(): DzPropertyGroup;
    getNumProperties(): number;
    getParent(): DzPropertyGroup;
    getPath(): string;
    getPreviousSibling(): DzPropertyGroup;
    getProperty(i: number): DzProperty;
    getRegion(): geometryregion_dz;
    getTree(): DzPropertyGroupTree;
    indexOfProperty(prop: DzProperty): number;
    isRegion(): boolean;
    movePropertyToIndex(prop: DzProperty, newIndex: number): boolean;
    setCollapsed(onOff: boolean): void;
    setUniquePropertyLabel(prop: DzProperty): void;
    sort(): void;

    // SIGNALS
    addedChild(newChild: DzPropertyGroup): void;
    childListChanged(): void;
    parentChanged(newParent: DzPropertyGroup): void;
    propertyVisiblityChanged(grp: DzPropertyGroup, prop: DzProperty): void;
    removedChild(child: DzPropertyGroup): void;
    treeChanged(): void;
}

/**
 * See Also: DzElement
 */
declare class DzPropertyGroupTree {
    findChild(name: string): DzPropertyGroup;
    findProperty(name: string): DzProperty;
    findPropertyByLabel(label: string): DzProperty;
    getAllPaths(): any[];
    getAllProperties(): any[];
    getDefaultGroup(): DzPropertyGroup;
    getFirstChild(): DzPropertyGroup;
    getOwner(): DzElement;
    isPrivate(): bool;
    setIsPrivate(onoff: boolean): void;
    sortGroups(): void;

    // SIGNALS
    childListChanged(): void;
    propertyVisiblityChanged(grp: DzPropertyGroup, prop: DzProperty): void;
    treeChanged(): void;
    treeSorted(): void;
}

/**
 * Provides a DzComboBox like widget with a custom popup designed for choosing a DzProperty .
 */
declare class DzPropertySelectionComboBox {
    clearPropertySelection(): void;
    getExcludeList(): any[];
    getNodes(): any[];
    getSelectedProperty(): DzProperty;
    hidePopup(): void;
    setEditMode(onOff: boolean): void;
    setExcludeList(properties: any[]): void;
    setMorphOnly(onOff: boolean): void;
    setNode(node: DzNode): void;
    setNodes(nodes: any[]): void;
    setNumericOnly(onOff: boolean): void;
    setPopUpHeight(height: number): void;
    setPopUpMinWidth(width: number): void;
    setPrivateOnly(onOff: boolean): void;
    setPublicOnly(onOff: boolean): void;
    setSelectedProperty(prop: DzProperty): void;
    setShowHidden(onOff: boolean): void;
    setTransformOnly(onOff: boolean): void;
    showPopup(): void;

    // SIGNALS
    propertySelectionChanged(): void;
}

/**
 * Property classes should use this to pass the options supported by the class.
 */
declare class DzPropertySettings {
}

/**
 * An asset save filter for saving a Puppeteer Preset in the DSON format. See Also: Sample: Save a Puppeteer Preset
 */
declare class DzPuppeteerAssetFilter {
}

/**
 * Provides a button that can be “pushed” (clicked, pressed, released, etc) in order to execute a command or answer a question.
 */
declare class DzPushButton {
    autoDefault(): boolean;
    buttonStyle: ButtonStyle;
    buttonTextFormat: number;
    collapseEmptySpace: boolean;
    default: boolean;
    displayDownArrow: boolean;
    downArrowMetric: string;
    downArrowPrimitive: string;
    elideMode: TextElideMode;
    flat: boolean;
    iconMetric: string;
    minimumWidthText: string;
    primitive: string;
    sizedFromIcon: boolean;
    textStyle: string;

    setCheckable(yesNo: boolean): void;
    setToggleButton(yesNo: boolean): void;

    // SIGNALS
    buttonStyleChanged(style: ButtonStyle): void;
    buttonTextFormatChanged(format: number): void;
    collapseEmptySpaceChanged(onOff: boolean): void;
    displayDownArrowChanged(displayArrow: boolean): void;
    downArrowMetricChanged(name: string): void;
    downArrowPrimitiveChanged(name: string): void;
    elideModeChanged(mode: TextElideMode): void;
    iconMetricChanged(name: string): void;
    primitiveChanged(name: string): void;
    sizedFromIconChanged(onOff: boolean): void;
    textStyleChanged(name: string): void;
}

/**
 * A specialization of DzModifier that moves the position of vertices in the geometry of an object along the normals of the base shape of the object. This modifier is applied according to a weight that is supplied by a value control. This weight defines the amplitude by which a given vertex is linearly moved along its normal - i.e., an offset distance from the surface of a mesh. Attenuating the influence of the weight, at a per vertex level, is supported through the use of a weight map. See Also: DzObject :: findModifier () DzWeightMap
 */
declare class DzPushModifier {
    assetAuthor(): DzAuthor;
    assetFileRevision: DzVersion;
    assetId: string;
    assetModifiedDate: Date;
    assetNeedSave: boolean;
    assetSource: DzUri;
    assetUri: DzUri;

    getInfluenceWeights(): DzWeightMap;
    getValueControl(): DzFloatProperty;
    invalidateInfluenceWeights(): void;
    isPostSmooth(): boolean;
    modifyAsset(): boolean;
    modifyAsset(newUri: DzUri): boolean;
    setInfluenceWeights(map: DzWeightMap): DzError;
    setToPostSmooth(arg0: boolean): void;

    // SIGNALS
    assetModified(): void;
    assetWasSaved(): void;
    weightListChanged(): void;
    weightsChanged(): void;
}

/**
 * Class for importing files in Poser formats; .pz3, *.pz2, *.cr2, *.lt2, *.cm2, *.pp2, *.fc2, *.hd2, *.hr2, *.mc6, .pzz, *.p2z, *.crz, *.ltz, *.cmz, *.ppz, *.fcz, *.hdz, *.hrz, *.mcz See Also: DzImportMgr :: findImporterByClassName () DzImportMgr :: findImporter ()
 */
declare class DzPZ3Importer {
}

/**
 * TODO: Add detailed description.
 */
declare class DzQuat {
    w(): number;
    x: number;
    y: number;
    z: number;

    equals(quat: DzQuat, tolerance: number): boolean;
    getAngleOfRotation(): number;
    getAxisOfRotation(): DzVec3;
    getValue(axis1: number, axis2: number, axis3: number): DzVec3;
    getXAxis(): DzVec3;
    getYAxis(): DzVec3;
    getZAxis(): DzVec3;
    identity(): DzQuat;
    inverse(): DzQuat;
    invert(): void;
    isIdentity(): boolean;
    makeClosest(quat: DzQuat): void;
    makeIdentity(): void;
    multiply(quat: DzQuat): DzQuat;
    multVec(vec: DzVec3): DzVec3;
    normalize(): void;
    scaleAngle(val: number): void;
    setValue(axis: number, radians: number): void;
    setValue(axis1: number, axis2: number, axis3: number, angles: DzVec3): void;
    setValue(axis: DzVec3, radians: number): void;
    setValue(x: number, y: number, z: number, w: number, normalize: boolean): void;
    slerp(rot0: DzQuat, rot1: DzQuat, t: number): DzQuat;
    toString(): string;
}

/**
 * DzRadioButton and DzCheckBox are both option buttons (e.g. they can be checked or unchecked). They differ in how the available choices are restricted. A DzCheckBox is used to define several choices that can all co-exist at the same time (e.g. “many of many”). While a DzRadioButton is used to provide several choices, where only one can be ultimately chosen (e.g. “one of many”). The easiest way to implement a “one of many” type choice is to create radio buttons as children of a DzButtonGroup . Example:
 */
declare class DzRadioButton {
    checked(): boolean;
}

/**
 * This error is thrown by the interpreter to indicate that a numeric value has exceeded the allowable range. See the ECMA script specification for more information.
 */
declare class RangeError {
}

/**
 * This is the script counterpart to the QRect type used in the C++ SDK. A Rect object is a two dimensional representation of a rectangle. Attention: Inheritance will change to Object in a pending update.
 */
declare class Rect {
    bottom(): number;
    center: Point;
    height: number;
    left: number;
    right: number;
    top: number;
    width: number;
    x: number;
    y: number;

    contains(rect: Rect): boolean;
    intersection(rect: Rect): Rect;
    intersects(rect: Rect): boolean;
    isEmpty(): boolean;
    isNull(): boolean;
    moveBottom(pos: number): void;
    moveBy(dx: number, dy: number): void;
    moveLeft(pos: number): void;
    moveRight(pos: number): void;
    moveTop(pos: number): void;
    normalize(): void;
    union(rect: Rect): Rect;
}

/**
 * Instances of DzRefCountedItem are objects that are intended to be shared between multiple owners. Each owner references the object when taking ownership, and dereference the object when it no longer needs the object. The object keeps an internal reference count, and when no other objects are referencing the object (i.e. the reference count reaches zero) the object will delete itself. Attention: Although this class is not directly exposed to DAZ Script, it is important to document the existence of it - for a proper understanding of the classes that also derive from it.
 */
declare class DzRefCountedItem {
}

/**
 * This error is thrown by the interpreter to indicate that an invalid reference has been detected. See the ECMA script specification for more information.
 */
declare class ReferenceError {
}

/**
 * This is the script counterpart to the QRegExp type used in the C++ SDK. A RegExp object is a regular expression. Regular expressions are patterns used to perform searches in, or replace text in, strings. Regular expressions can be created in DAZScript directly, or via the constructor. The following example shows creating expressions via the two methods, both of which result in identical expressions. Recommended Reading: Reference - Regular-Expressions.info Example:
 */
declare class RegExp {
    global(): boolean;
    ignoreCase: boolean;
    lastIndex: number;
    multiline: boolean;
    source: string;
    capturedTexts: any[];
    empty: boolean;
    matchedLength: number;
    valid: boolean;

    exec(string: string): any[];
    test(string: string): boolean;
    toString(): string;
    cap(which: number): string;
    exactMatch(text: string): boolean;
    pos(which: number): number;
    search(text: string): number;
    searchRev(text: string): number;
}

/**
 * Implements a standard RenderMan interface for the scene to render itself through an offline renderer.
 */
declare class DzRenderer {
    compileShader(shaderPath: string): string;
    customRender(handler: DzRenderHandler, camera: DzCamera, lights: any[], nodes: any[], opt: DzRenderOptions): boolean;
    getCurrentNode(): DzNode;
    getIPRRenderHandler(): iprrenderhandler_dz;
    getName(): string;
    getRenderCamera(): DzCamera;
    getRendererMode(): DzRendererMode;
    getShaderCompilerPath(): string;
    getShaderExtension(): string;
    getShaderFileName(shaderName: string): string;
    getShaderInfo(shaderPath: string): DzShaderDescription;
    getShaderPath(shaderName: string, withExtension: boolean): string;
    getShaderSearchPaths(): any[];
    getTextureUtilityPath(): string;
    isRendering(): boolean;
    killRender(): void;
    prepareImage(img: DzTexture, filename: string): void;
    processShaderName(shaderName: string): string;
    render(handler: DzRenderHandler, camera: DzCamera, opt: DzRenderOptions): boolean;
    saveBakeImage(opt: DzBakerOptions, wait: boolean): void;
    setIPRRenderHandler(handler: iprrenderhandler_dz): void;
    setRenderCamera(camera: DzCamera): void;
    stopBaking(): void;
    textureConvert(handler: DzRenderHandler, camera: DzCamera, opt: textureconvertoroptions_dz): boolean;

    // SIGNALS
    aboutToRender(renderer: DzRenderer): void;
    imagePrepared(img: DzTexture, filename: string): void;
    IPRRenderHandlerChanged(renderer: DzRenderer, handler: iprrenderhandler_dz): void;
    rendererModeChanged(renderer: DzRenderer): void;
    renderFinished(renderer: DzRenderer): void;
    shapeRenderBeginning(shape: DzShape): void;
    shapeRenderFinished(shape: DzShape): void;
}

/**
 * Many render engines provide a single mode of operation; i.e. the engine is either biased or it is physically based. However, as the development of a render engine evolves, it may provide more than one mode of operation, and each mode may provide a different set of features.
 */
declare class DzRendererMode {
    defaultMaterialClassName(): string;
    hasFeatures(): boolean;
    isBiased(): boolean;
    isPhysicallyBased(): boolean;
    isRenderManCompliant(): boolean;
    supportedLanguages(): any[];
    supportsAdvancedCamera(): boolean;
    supportsCameraBlades(): boolean;
    usesCatmarkLimitSurface(): boolean;
}

/**
 * Render handler classes are responsible for the settings of a render, as well as collecting the final image data passed back from the renderer. See Also: DzRenderer :: render (), DzRenderer :: customRender (), Dz3DViewport :: hardwareRender (), Dz3DViewport :: renderThumbnail (), pbufferview_dz :: hardwareRender (), pbufferview_dz :: renderThumbnail ()
 */
declare class DzRenderHandler {
    getBackColor(): { r: number, g: number, b: number, a: number };
    getCropWindow(): Rect;
    getNumFrames(): number;
    getSize(): Size;
    getStartingTime(): number;
    getUseCropWindow(): boolean;
    setBackColor(color: { r: number, g: number, b: number, a: number }): void;
    setCropWindow(window: Rect): void;
    setUseCropWindow(onOff: boolean): void;
}

/**
 * Responsible for the management of renderers, and more generally the process of performing a render. There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getRenderMgr (). See Also: Global :: App
 */
declare class DzRenderMgr {
    getIconSuffix(): string;
    getMetaXmlFileName(imageName: string, basenameOnly: boolean): string;
    getRenderBaseFileName(imageName: string, basenameOnly: boolean): string;
    getRenderIconFileName(imageName: string, basenameOnly: boolean): string;
    addRenderDirectory(directory: string, saveSetting: boolean): void;
    doIPRRender(camera: DzCamera, renderHandler: DzRenderHandler, opt: DzRenderOptions): boolean;
    doRender(opt: DzRenderOptions): boolean;
    findRenderer(className: string): DzRenderer;
    getActiveRenderer(): DzRenderer;
    getBaseAndRelativePath(absPath: string): any[];
    getLastSavedRenderPath(): string;
    getNumRenderDirectories(): number;
    getNumRenderers(): number;
    getOptionHelper(): DzElement;
    getRenderDirectoryPath(which: number): string;
    getRenderElementObjects(): any[];
    getRenderer(which: number): DzRenderer;
    getRendererList(): any[];
    getRenderOptions(): DzRenderOptions;
    hasRender(): boolean;
    isRendering(): boolean;
    rebuildRenderElements(): void;
    removeAllRenderDirectories(): void;
    removeRenderDirectory(directory: string): boolean;
    restoreDefaultRenderOptions(): void;
    saveLastRender(): string;
    setActiveRenderer(renderer: DzRenderer): void;
    showRenderDialog(): void;
    stopIPRRender(): void;

    // SIGNALS
    activeRendererChanged(renderer: DzRenderer): void;
    activeRendererIPRRenderHandlerChanged(renderer: DzRenderer, handler: iprrenderhandler_dz): void;
    doIPRRenderStop(): void;
    hasRenderChanged(state: boolean): void;
    IPRRenderStarted(): void;
    IPRRenderStopped(): void;
    renderDirectoryListChanged(): void;
    renderElementsListChanged(): void;
    rendererAdded(renderer: DzRenderer): void;
    rendererIPRRenderHandlerChanged(renderer: DzRenderer, handler: iprrenderhandler_dz): void;
    rendererModeChanged(renderer: DzRenderer): void;
    renderFinished(succeeded: boolean): void;
    renderFolderChanged(): void;
    renderOptionDefaultsRestored(): void;
    renderStarting(): void;
}

/**
 * The RenderOptions class is responsible for the inclusion/exclusion of certain aspects of a render.
 */
declare class DzRenderOptions {
    aspect(): number;
    aspectHeight: number;
    aspectWidth: number;
    doubleSided: boolean;
    endTime: number;
    gain: number;
    gamma: number;
    gammaCorrection: GammaCorrection;
    imageSize: Size;
    isAspectConstrained: boolean;
    isCurrentFrameRender: boolean;
    lastRenderImgFilename: string;
    lastRenderMovFilename: string;
    lastRenderSerFilename: string;
    motionBlurOffset: number;
    motionBlurPct: number;
    motionBlurSamples: number;
    openGLPasses: number;
    pixelFilter: PixelFilter;
    rayTraceDepth: number;
    renderImgFilename: string;
    renderImgToId: RenderImgTarget;
    renderMovFilename: string;
    renderMovToId: RenderMovTarget;
    renderSerFilename: string;
    renderStyle: RenderStyle;
    renderType: RenderType;
    renderViewport: boolean;
    shadingRate: number;
    shadowSamples: number;
    showPreview: boolean;
    startTime: number;
    useGLSL: boolean;
    useMotionBlur: boolean;
    xFilterWidth: number;
    xPixelSamples: number;
    yFilterWidth: number;
    yPixelSamples: number;

    applyChanges(): void;
    copyFrom(opt: DzRenderOptions): void;
    gammaCorrectColor(color: DzFloatColor): DzFloatColor;
    resetOptions(): void;
    restoreDefaultSettings(): void;
    setAspectRatio(widthRatio: number, heightRatio: number): void;
    setToDefaults(): void;

    // SIGNALS
    aspectChanged(val: number): void;
    aspectChanged(w: number, h: number): void;
    aspectConstrainChanged(onOff: boolean): void;
    defaultsRestored(): void;
    doubleSidedChanged(onOff: boolean): void;
    endTimeChanged(time: number): void;
    gainChanged(gain: number): void;
    gammaChanged(gamma: number): void;
    gammaCorrectionChanged(gc: GammaCorrection): void;
    imageSizeChanged(size: Size): void;
    motionBlurOffsetChanged(offset: number): void;
    motionBlurPctChanged(pct: number): void;
    motionBlurSamplesChanged(samples: number): void;
    openGLPassesChanged(passes: number): void;
    pixelFilterChanged(filter: PixelFilter): void;
    rayTraceDepthChanged(depth: number): void;
    renderCurrentFrameChanged(onOff: boolean): void;
    renderImgFilenameChanged(filename: string): void;
    renderImgTargetChanged(id: RenderImgTarget): void;
    renderMovFilenameChanged(filename: string): void;
    renderMovTargetChanged(id: RenderMovTarget): void;
    renderSerFilenameChanged(filename: string): void;
    renderStyleChanged(style: RenderStyle): void;
    renderTypeChanged(type: RenderType): void;
    renderViewportChanged(onOff: boolean): void;
    settingsChanged(): void;
    shadingRateChanged(rate: number): void;
    shadowSamplesChanged(samples: number): void;
    showPreviewChanged(onoff: boolean): void;
    startTimeChanged(time: number): void;
    useGLSLChanged(onOff: boolean): void;
    useMotionBlurChanged(onOff: boolean): void;
    xFilterWidthChanged(width: number): void;
    xPixelSamplesChanged(samples: number): void;
    yFilterWidthChanged(width: number): void;
    yPixelSamplesChanged(samples: number): void;
}

/**
 * An asset save filter for saving a Render Settings Preset in the DSON format. See Also: Sample: Save a Render Settings Preset
 */
declare class DzRenderSettingsAssetFilter {
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureComponent instead.
 */
declare class DzRotateManip {
    degrees(): number;

    getDegrees(): number;
    getRotation(): Rotation;
    setDegrees(deg: number): void;
    setRotation(rot: Rotation): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzRotationOrder {
    firstAxis(): number;
    order: number;
    secondAxis: number;
    thirdAxis: number;

    setOrder(firstAxis: number, secondAxis: number, thirdAxis: number): void;
    toString(): string;
}

/**
 * This class provides the ability to define RSL shaders for the elements that can use them ( DzShaderMaterial , DzShaderLight , DzShaderCamera ). Optimizations: Two methods in this class that should not be overlooked are setActiveInShadowPass () and setOnlyInShadowPass (), as they can have a significant impact on render times. In the context of Surface shaders, the data members set by these methods are used to identify whether the shader participates during the shadow [map] pass - the pass for each contributing light in the scene that indicates the use of Deep Shadow Maps for shadows. This affords developers a couple of key benifits: One key benifit is the ability to use a single Displacement shader in both the shadow pass as well as the beauty pass. Not only does this alleviate the duplication of code, but by utilizing a Displacement shader for any bump/diplacement operations, rendering times become much faster than performing the same operations in a Surface shader. This is due to the frequency that the shader code is executed. Displacement shaders are evaluated once, at the begining of a pass, and a caching mechanism for the displaced geometry is used as the render progresses. When the same code is placed in a Surface shader, the bump/displacment calculations are performed at every evaluation of the surface. Another key benifit is the ability to use a highly optimized Surface shader during the shadow [map] pass, which can have a significant impact on the time required to generate a shadow map - and thus complete the render. In the context of Light shaders, the data members set by these methods are used to identify whether this shader participates when the DzLight :: ShadowType indicates shadowing is used. This affords developers the benifit of being able to use Light shaders that are optimized for either condition. Property Naming: Standard Shader and Materials Presets make an effort to copy as much as possible from one element to the next via DzElement :: copyFrom (). In order for this to occur, the properties must match in both name and type. Provided below are the names and types used by DzDefaultMaterial , DzLight , DzDistantLight , DzSpotLight and DzPointLight in the event that you would like use properties that will work with the copyFrom() method. Default Material: Default Lights: Default Camera: Name Type Name Type Diffuse Color DzColorProperty Negative Bump DzFloatProperty Diffuse Strength DzFloatProperty Positive Bump DzFloatProperty Glossiness DzFloatProperty Displacement Strength DzFloatProperty Specular Color DzColorProperty Minimum Displacement DzFloatProperty Specular Strength DzFloatProperty Maximum Displacement DzFloatProperty Multiply Specular Through Opacity DzBoolProperty Reflection Color DzColorProperty Ambient Color DzColorProperty Reflection Strength DzFloatProperty Ambient Strength DzFloatProperty Refraction Color DzColorProperty Opacity Strength DzFloatProperty Refraction Strength DzFloatProperty Bump Strength DzFloatProperty Index of Refraction DzFloatProperty Name Type Color DzColorProperty Intensity DzFloatProperty Shadow Type DzEnumProperty Shadow Bias DzFloatProperty Shadow Softness DzFloatProperty Illumination DzEnumProperty Spread Angle DzFloatProperty Name Type Focal Length DzFloatProperty DOF DzBoolProperty Depth of Field DzFloatProperty Aperature DzFloatProperty Samples: rispec_constant_shader_definition - The definition file for the standard RenderMan Constant Surface Shader, that builds the properties displayed to users in the Surfaces tab (Advanced sub tab). ./samples/shader swapping/ See Also: rispec_constant_shader_preset - A [heavily commented] Shader Preset that applies a material definition script (below) for the standard RenderMan Constant Surface Shader. rispec_constant_material_definition - The definition file for the above, that builds the shader objects used by the render for the current material. rispec_constant_surface_shader - The RSL source for the standard RenderMan Constant Surface Shader. s_standard_render_time_script - The render-time script that sets various RiAttributes dependant on the values of properties provided to the user. Recommended Reading: The RenderMan Interface Specification (RISpec) - Pixar Animation Studios Advanced RenderMan: Creating CGI for Motion Pictures - (ISBN:1558606181) - Tony Apodaca and Larry Gritz 1999 RenderMan Companion: A Programmer's Guide to Realistic Computer Graphics - (ISBN:0201508680) - Steve Upstill 1989 Texturing & Modeling: A Procedural Approach (3rd Edition) - (ISBN:1558608486) - David S. Ebert, F. Kenton Musgrave, Darwyn Peachey, Ken Perlin, and Steve Worley 1998 3Delight Documentation - The 3Delight Team
 */
declare class DzRSLShader {
    addMappableProperty(prop: DzNumericProperty, token: string, mapToken: string): boolean;
    addMapProperty(prop: DzNumericProperty, mapToken: string): boolean;
    addShaderProperty(prop: DzProperty, token: string): boolean;
    findMapTokenByProperty(prop: DzNumericProperty): string;
    findProperty(name: string): DzProperty;
    findPropertyByToken(token: string): DzProperty;
    findTokenByProperty(prop: DzProperty): string;
    getDefinitionFile(): string;
    getNumProperties(): number;
    getOwner(): DzElement;
    getProperty(which: number): DzProperty;
    getPropertyList(): any[];
    getRenderTimeFile(): string;
    getShaderFile(): string;
    getShaderType(): ShaderType;
    isActiveInBakePass(): boolean;
    isActiveInBeautyPass(): boolean;
    isActiveInShadowPass(): boolean;
    isOnlyInShadowPass(): boolean;
    removeProperty(prop: DzProperty): boolean;
    removeProperty(name: string): boolean;
    setActiveInBakePass(yesNo: boolean): void;
    setActiveInBeautyPass(yesNo: boolean): void;
    setActiveInShadowPass(yesNo: boolean): void;
    setDefinitionFile(definitionFile: string, doOverride: boolean, runScript: boolean): boolean;
    setOnlyInShadowPass(yesNo: boolean): void;
    setRenderTimeFile(renderTimeFile: string): boolean;
    setShaderFile(shaderFile: string): boolean;
    setShaderType(shaderType: ShaderType): boolean;
    gammaCorrectColor(color: { r: number, g: number, b: number, a: number }): DzVec3;
    setFloatAttrib(attrib: string, token: string, val: number): void;
    setIntegerAttrib(attrib: string, token: string, val: number): void;
    setColorAttrib(attrib: string, token: string, r: number, g: number, b: number, isFloat: boolean): void;
    setStringAttrib(attrib: string, token: string, val: string): void;
    setPointAttrib(attrib: string, token: string, vec: DzVec3): void;
    setVectorAttrib(attrib: string, token: string, vec: DzVec3): void;
    setNormalAttrib(attrib: string, token: string, vec: DzVec3): void;
    setMatrixAttrib(attrib: string, token: string, mtx: DzMatrix4): void;
    setFloatToken(token: string, val: number): void;
    setIntegerToken(token: string, val: number): void;
    setColorToken(token: string, val: { r: number, g: number, b: number, a: number }): void;
    setStringToken(token: string, val: string): void;
    setPointToken(token: string, vec: DzVec3): void;
    setVectorToken(token: string, vec: DzVec3): void;
    setNormalToken(token: string, vec: DzVec3): void;
    setMatrixToken(token: string, mtx: DzMatrix4): void;
    makeCubeFaceEnvironment(px: string, nx: string, py: string, ny: string, pz: string, nz: string, tex: string, fov: number, filter: PixelFilter, swidth: number, twidth: number, tokens: any[], params: any[]): void;
    makeLatLongEnvironment(pic: string, tex: string, filter: PixelFilter, swidth: number, twidth: number, tokens: any[], params: any[]): void;
    makeShadow(pic: string, tex: string, tokens: any[], params: any[]): void;
    makeTexture(pic: string, tex: string, swrap: string, twrap: string, filter: PixelFilter, swidth: number, twidth: number, tokens: any[], params: any[]): void;
    makeBump(pic: string, tex: string, swrap: string, twrap: string, filter: PixelFilter, swidth: number, twidth: number, tokens: any[], params: any[]): void;
    addTransformBegin(): void;
    addTransformEnd(): void;
    addScheduledTransformEnd(): void;
    addConcatTransform(transform: DzMatrix4): void;
    addCoordinateSystem(space: string): void;
    addCoordSysTransform(space: string): void;
    addIdentity(): void;
    addRotate(angle: number, dx: number, dy: number, dz: number): void;
    addScale(dx: number, dy: number, dz: number): void;
    addScopedCoordinateSystem(space: string): void;
    addSkew(angle: number, dx1: number, dy1: number, dz1: number, dx2: number, dy2: number, dz2: number): void;
    addTransform(transform: DzMatrix4): void;
    addTranslate(dx: number, dy: number, dz: number): void;

    // SIGNALS
    propertyAdded(prop: DzProperty): void;
    propertyListChanged(): void;
    propertyRemoved(prop: DzProperty): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzSaveAsSupportAction {
}

/**
 * Deprecated Save filters save out a subset of scene settings such as poses, light sets, camera sets, etc. in DAZ Script format. Script based presets are deprecated in favor of those in the DAZ Scene Object Notation (DSON) format. See Also: DzAssetIOMgr DzAssetIOFilter
 */
declare class DzSaveFilter {
    getDescription(): string;
    getLoadSavePath(): string;
    setLoadSavePath(path: string): void;
    writeFile(filename: string, mode: ScriptFileMode): DzError;
    writeFile(filename: string, mode: ScriptFileMode, options: DzFileIOSettings): DzError;
}

/**
 * Deprecated This class is responsible for the management of save filters that produce script-based presets - DzSaveFilter (deprecated) . Script based presets are deprecated in favor of those in the DAZ Scene Object Notation (DSON) format. There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getSaveFilterMgr (). See Also: Global :: App DzAssetIOMgr DzAssetIOFilter
 */
declare class DzSaveFilterMgr {
    findFilter(className: string): number;
    getFilter(i: number): DzSaveFilter;
    getFilterName(i: number): string;
    getNumFilters(): number;
    doSave(filterIndex: number, dir: string): DzError;
    getSavePath(): string;
    writeFile(mode: ScriptFileMode, fileName: string, filterName: string): DzError;
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureComponent instead.
 */
declare class DzScaleManip {
    heightScale(): number;
    widthScale: number;

    setScale(w: number, h: number): void;
}

/**
 * There is only one of these objects in the application. It is the communication hub between the core code and the interface, so it tracks all nodes, skeletons, lights, cameras, etc. that become part of the scene. This object is directly available using the Global :: Scene variable.
 */
declare class DzScene {
    assetId(): string;
    assetNeedSave: boolean;
    assetUri: DzUri;

    executeNodePostCreateScript(node: DzNode, settingsBase: string): boolean;
    getLabelNumber(label: string): string;
    getNameNumber(name: string): string;
    stripLabelNumber(label: string): string;
    stripNameNumber(name: string): string;
    addDataItem(item: DzSceneData): DzError;
    addNode(node: DzNode): boolean;
    addWSModifier(modifier: wsmodifier_dz, index: number): DzError;
    beginTimeEdit(): void;
    clear(): void;
    findCamera(name: string): DzCamera;
    findCameraByLabel(label: string): DzCamera;
    findDataItem(name: string): DzSceneData;
    findLight(name: string): DzLight;
    findLightByLabel(label: string): DzLight;
    findMaterialByElementID(id: number): DzMaterial;
    findModifierByElementID(id: number): DzModifier;
    findNode(name: string): DzNode;
    findNodeByElementID(id: number): DzNode;
    findNodeByLabel(label: string): DzNode;
    findNodeIndex(node: DzNode): number;
    findObjectByElementID(id: number): DzObject;
    findShapeByElementID(id: number): DzShape;
    findSingletonNode(guidStr: string): DzNode;
    findSkeleton(name: string): DzSkeleton;
    findSkeletonByLabel(label: string): DzSkeleton;
    findSkeletonIndex(skeleton: DzSkeleton): number;
    finishTimeEdit(): void;
    getAnimRange(): DzTimeRange;
    getAssetLoadPath(): string;
    getAudio(): DzAudioClip;
    getAudioStartFrame(): number;
    getAuthor(): DzAuthor;
    getBackdrop(): DzBackdrop;
    getBoundingBox(flags: number): DzBox3;
    getCamera(index: number): DzCamera;
    getCameraList(): any[];
    getDataItem(index: number): DzSceneData;
    getDataItemList(): any[];
    getDefaultKeyInterpolationType(): InterpolationType;
    getFilename(): string;
    getFrame(): number;
    getHighlightNode(): DzNode;
    getLight(index: number): DzLight;
    getLightList(): any[];
    getNode(index: number): DzNode;
    getNodeList(): any[];
    getNumCameras(): number;
    getNumDataItems(): number;
    getNumLights(): number;
    getNumNodes(): number;
    getNumSelectedCameras(): number;
    getNumSelectedLights(): number;
    getNumSelectedNodes(): number;
    getNumSelectedSkeletons(): number;
    getNumSelectedTimeRanges(): number;
    getNumSkeletons(): number;
    getNumStorablesInScene(): number;
    getNumWSModifiers(): number;
    getPlayRange(): DzTimeRange;
    getPreviewLights(): boolean;
    getPrimarySelection(): DzNode;
    getSelectedCamera(index: number): DzCamera;
    getSelectedCameraList(): any[];
    getSelectedLight(index: number): DzLight;
    getSelectedLightList(): any[];
    getSelectedNode(index: number): DzNode;
    getSelectedNodeList(): any[];
    getSelectedSkeleton(index: number): DzSkeleton;
    getSelectedSkeletonList(): any[];
    getSkeleton(index: number): DzSkeleton;
    getSkeletonList(): any[];
    getSortedLightList(): any[];
    getTime(): number;
    getTimeStep(): number;
    getUniqueDataItemName(dataName: string): string;
    getUniqueTopLevelLabel(label: string, node: DzNode): string;
    getUniqueTopLevelName(name: string, node: DzNode): string;
    getWSModifier(index: number): wsmodifier_dz;
    getWSModifierList(): any[];
    invalidate(): void;
    invalidateLightSorting(): void;
    isClearing(): boolean;
    isDAZLoading(): boolean;
    isLoading(): boolean;
    isLoopingEnabled(): boolean;
    isPlaying(): boolean;
    loadScene(filename: string, method: DzOpenMethod): DzError;
    loopPlayback(onOff: boolean): void;
    markChanged(): void;
    moveNodeToIndex(child: DzNode, index: number): DzError;
    moveNodeToIndex(nodeIndex: number, newNodeIndex: number): DzError;
    needsSave(): boolean;
    pause(): void;
    play(realtime: boolean): void;
    protectSceneSourceFile(): void;
    removeAllCameras(): void;
    removeAllLights(): void;
    removeDataItem(item: DzSceneData): DzError;
    removeNode(node: DzNode): boolean;
    removeSelected(): void;
    removeWSModifier(modifier: wsmodifier_dz): DzError;
    saveScene(filename: string): DzError;
    saveThumbnailImage(filename: string): void;
    saveThumbnailImage(filename: string, options: DzFileIOSettings): void;
    selectAllNodes(onOff: boolean): void;
    selectAllSkeletons(onOff: boolean): void;
    selectAllTime(onOff: boolean): void;
    setAnimRange(range: DzTimeRange): void;
    setAssetLoadPath(absolutePath: string): void;
    setAudio(audio: DzAudioClip, startFrame: number): void;
    setBackdrop(backdrop: DzBackdrop): void;
    setDefaultKeyInterpolationType(type: InterpolationType): void;
    setFrame(frame: number): void;
    setHighlightNode(node: DzNode): void;
    setPlayRange(range: DzTimeRange): void;
    setPreviewLights(onoff: boolean): void;
    setPrimarySelection(node: DzNode): boolean;
    setTime(time: number): void;
    setTimeStep(time: number): void;
    sortNodesByHierarchy(): void;
    stepTime(nFrames: number, forward: boolean): void;
    update(): void;
    saveThumbnail(filename: string): void;

    // SIGNALS
    aboutToRemoveNode(node: DzNode): void;
    aboutToRender(r: DzRenderer): void;
    animRangeChanged(range: DzTimeRange): void;
    assetModified(): void;
    assetWasSaved(): void;
    backdropChanged(): void;
    cameraAdded(node: DzCamera): void;
    cameraListChanged(): void;
    cameraRemoved(node: DzCamera): void;
    cameraSelectionListChanged(): void;
    currentTimeChanged(oldTime: number, newTime: number): void;
    defaultKeyInterpolationTypeChanged(type: InterpolationType): void;
    drawnDataChanged(): void;
    highlightNodeChanged(node: DzNode): void;
    lightAdded(node: DzLight): void;
    lightListChanged(): void;
    lightRemoved(node: DzLight): void;
    lightSelectionListChanged(): void;
    loopPlaybackChanged(onOff: boolean): void;
    materialListChanged(): void;
    materialSelectionChanged(): void;
    nodeAdded(node: DzNode): void;
    nodeListChanged(): void;
    nodeRemoved(node: DzNode): void;
    nodeSelectionListChanged(): void;
    playbackFinished(): void;
    playbackStarted(): void;
    playRangeChanged(range: DzTimeRange): void;
    primarySelectionChanged(node: DzNode): void;
    renderFinished(r: DzRenderer): void;
    sceneCleared(): void;
    sceneClearStarting(): void;
    sceneFilenameChanged(newName: string): void;
    sceneLoaded(): void;
    sceneLoadStarting(): void;
    sceneSaved(filename: string): void;
    sceneSaveStarting(filename: string): void;
    sceneTopologyChanged(): void;
    singletonNodeAdded(node: DzNode): void;
    skeletonAdded(node: DzSkeleton): void;
    skeletonListChanged(): void;
    skeletonRemoved(node: DzSkeleton): void;
    skeletonSelectionListChanged(): void;
    timeChanged(time: number): void;
    timeChanging(newTime: number): void;
    timeSelectionChanged(): void;
    timeStepChanged(time: number): void;
    wsModifierAdded(modifier: wsmodifier_dz): void;
    wsModifierRemoved(modifier: wsmodifier_dz): void;
    wsModifierStackChanged(): void;
}

/**
 * An asset save filter for saving a Scene in the DSON format. See Also: Sample: Save a Scene
 */
declare class DzSceneAssetFilter {
}

/**
 * Implements a custom data item that allows named data to be associated with the scene. See Also: DzScene :: addDataItem () DzScene :: removeDataItem () DzScene :: getUniqueDataItemName () DzScene :: findDataItem () DzScene :: getNumDataItems () DzScene :: getDataItem () DzScene :: getDataItemList ()
 */
declare class DzSceneData {
}

/**
 * TODO: Add detailed description.
 */
declare class DzSceneHelper {
    collectNodes(selectedOnly: boolean, boneTopSelected: boolean, boneSkeleton: boolean): any[];
    createLink(bone: DzNode, propertyName: string, controlBone: DzNode, controllerName: string, type: number, scalar: number, addend: number): DzERCLink;
    createMorph(bone: DzNode, name: string, deltas: any[], overwrite: boolean): DzMorph;
    findControlProperty(propertyName: string, node: DzNode, recurse: boolean, nameLabelMatch: boolean): DzProperty;
    findProperty(propName: string, elem: DzElement): DzProperty;
    findPropertyByInternalName(internalName: string, elem: DzElement): DzProperty;
    findPropertyByLabel(label: string, elem: DzElement): DzProperty;
    findPropertyInGroup(propertyName: string, group: DzPropertyGroup, traverse: boolean, recurse: boolean, nameLabelMatch: boolean): DzProperty;
    findPropertyOnMaterial(propName: string, material: DzMaterial): DzProperty;
    findPropertyOnMaterialByInternalName(internalName: string, material: DzMaterial): DzProperty;
    findPropertyOnMaterialByLabel(label: string, material: DzMaterial): DzProperty;
    findPropertyOnNode(propName: string, node: DzNode): DzProperty;
    findPropertyOnNodeByInternalName(internalName: string, node: DzNode): DzProperty;
    findPropertyOnNodeByLabel(label: string, node: DzNode): DzProperty;
    getDisplayMaterial(prop: DzProperty): DzMaterial;
    getDisplayNode(prop: DzProperty): DzNode;
    getErcController(controlledProp: DzProperty, controllingProp: DzProperty): DzERCLink;
    getInternalName(prop: DzProperty): string;
    getLabel(prop: DzProperty): string;
    getMaterial(prop: DzProperty): DzMaterial;
    getMaterialName(prop: DzProperty): string;
    getMaterialType(prop: DzProperty): string;
    getMax(prop: DzProperty): number;
    getMin(prop: DzProperty): number;
    getNode(prop: DzProperty): DzNode;
    getNodeName(prop: DzProperty): string;
    getNodeType(prop: DzProperty): string;
    getPrivatePropertiesOnNode(prop: DzProperty): any[];
    getPrivatePropertiesOnNode(node: DzNode): any[];
    getPropertiesOnElement(elem: DzElement): any[];
    getPropertiesOnMaterial(prop: DzProperty, includeProviders: boolean): any[];
    getPropertiesOnMaterial(material: DzMaterial, includeProviders: boolean): any[];
    getPropertiesOnNode(prop: DzProperty, includeModifiers: boolean): any[];
    getPropertiesOnNode(node: DzNode, includeModifiers: boolean): any[];
    getRegionPropertiesOnNode(node: DzNode): any[];
    getRegionPropertiesRecurse(region: geometryregion_dz): any[];
    getUniqueMorphName(node: DzNode, name: string): string;
    helperCanRemove(prop: DzProperty): boolean;
    helperRemoveProperty(prop: DzProperty): boolean;
    isAtDefaultValue(prop: DzProperty): boolean;
    isControlledByTransform(prop: DzProperty, recurse: boolean): boolean;
    isDFormModProperty(prop: DzProperty): DzProperty;
    isLegacyJointProperty(prop: DzProperty): DzProperty;
    isLegacyProperty(prop: DzProperty): boolean;
    isMaterialProperty(prop: DzProperty): DzProperty;
    isModifierProperty(prop: DzProperty): DzProperty;
    isMorphProperty(prop: DzProperty): DzProperty;
    isNodeProperty(prop: DzProperty): DzProperty;
    isSimulationSettingsProviderProperty(prop: DzProperty): DzProperty;
    isTransform(prop: DzProperty): boolean;
    isTransformProperty(prop: DzProperty): DzProperty;
    setInternalName(prop: DzProperty, name: string): boolean;
    setMax(prop: DzProperty, max: number): void;
    setMin(prop: DzProperty, min: number): void;
    setMinMax(prop: DzProperty, min: number, max: number): void;
    setPropertyPath(prop: DzProperty, inPath: string): void;
    setUniqueName(node: DzNode, name: string): void;
}

/**
 * An asset save filter for saving a Scene Subset in the DSON format. See Also: Sample: Save a Scene Subset
 */
declare class DzSceneSubsetAssetFilter {
}

/**
 * An asset save filter for saving Figure/Prop Assets, or Dynamic Cloth Assets, for each object in the scene, in the DSON format. See Also: Sample: Save Scene Support Assets DzNodeSupportAssetFilter DzDynamicClothSupportAssetFilter
 */
declare class DzSceneSupportAssetFilter {
}

/**
 * TODO: Add detailed description.
 */
declare class DzScript {
    addScriptBinaryExtensionAsFilter(filter: DzFileFilter): void;
    addScriptBinaryExtensionsAsMultipleFilters(filter: DzFileFilter): void;
    addScriptBinaryExtensionsToFilter(filter: DzFileFilter): void;
    addScriptEncryptedBinaryExtensionAsFilter(filter: DzFileFilter): void;
    addScriptOpenExtensionsAsMultipleFilters(filter: DzFileFilter): void;
    addScriptOpenExtensionsToFilter(filter: DzFileFilter): void;
    addScriptSaveExtensionsAsMultipleFilters(filter: DzFileFilter): void;
    addScriptSaveExtensionsToFilter(filter: DzFileFilter): void;
    addScriptTextExtensionAsFilter(filter: DzFileFilter): void;
    addScriptTextExtensionsAsMultipleFilters(filter: DzFileFilter, includeDeprecated: boolean): void;
    addScriptTextExtensionsToFilter(filter: DzFileFilter, includeDeprecated: boolean): void;
    evaluate(code: string, context: QObject): any;
    getScriptExtensions(): any[];
    getScriptFile(filenameWithoutExtension: string): string;
    isScriptBinaryExtension(extension: string): boolean;
    isScriptBinaryFile(filename: string): boolean;
    isScriptExtension(extension: string): boolean;
    isScriptFile(filename: string): boolean;
    isScriptTextExtension(extension: string): boolean;
    isScriptTextFile(filename: string): boolean;
    legalizeName(str: string): string;
    addCode(code: string): void;
    addLine(line: string, indentLevel: number): void;
    addLines(code: string, indentLevel: number): void;
    call(_function: string, args: any[]): boolean;
    checkSyntax(): boolean;
    clear(): void;
    convertToDAZScript2(): boolean;
    errorLine(): number;
    errorMessage(): string;
    execute(): boolean;
    execute(args: any[]): boolean;
    getAuthor(): DzAuthor;
    getCode(): string;
    getFilename(): string;
    getLastStatus(): boolean;
    getScriptLanguage(): ScriptLanguage;
    getScriptType(): string;
    getScriptVersion(): DzVersion;
    getShouldReuseInterpreter(): boolean;
    isEmpty(): boolean;
    isEncrypted(): boolean;
    loadFromFile(filename: string, convert: boolean): boolean;
    makeEncrypted(): void;
    result(): any;
    saveFile(filename: string, mode: ScriptFileMode, filetype: string, version: DzVersion): DzError;
    saveFile(filename: string): DzError;
    setCode(code: string): void;
    setReuseInterpreter(onoff: boolean): void;
    stackTrace(): any[];
    wasConverted(language: ScriptLanguage): boolean;
    saveToFile(filename: string, mode: ScriptFileMode, filetype: string): DzError;
}

/**
 * A global transient variable named Action , which refers to the DzScriptAction that invoked the execution of the script, is provided to the script in the global context at runtime. Attempts to use this global variable outside the associated script will result in a ReferenceError . See Also: DzAction :: triggerSettings Since: 4.7.1.98
 */
declare class DzScriptAction {
}

/**
 * All DzScripts are executed in the context of a DzScriptContext instance - therefore, all the properties and methods on DzScriptContext are accessible to a script as global functions and variables. It will usually not be necessary for a script to create or use this class directly.
 */
declare class DzScriptContext {
    acceptUndo(caption: string): void;
    backgroundProgressIsActive(): boolean;
    backgroundProgressIsCancelled(): boolean;
    beginNodeSelectionHold(): void;
    beginUndo(): void;
    cancelBackgroundProgress(): void;
    cancelProgress(): void;
    cancelUndo(): void;
    clearBusyCursor(): void;
    clearNodeSelectionHolds(): void;
    clearOverrideCursor(): void;
    clearUndoStack(): void;
    dropNodeSelectionHold(): void;
    dropUndo(): void;
    finishBackgroundProgress(): void;
    finishBackgroundProgressWithDetail(): any;
    finishProgress(): void;
    finishProgressWithDetail(): any;
    getArguments(): any[];
    getErrorMessage(errCode: number): string;
    getObjectParent(obj: QObject): QObject;
    getScriptAuthor(): DzAuthor;
    getScriptFileName(): string;
    getScriptType(): string;
    getScriptVersionString(): string;
    pointersAreEqual(ptr1: QObject, ptr2: QObject): boolean;
    processEvents(): void;
    progressIsActive(): boolean;
    progressIsCancelled(): boolean;
    restoreNodeSelectionHold(): void;
    setBackgroundProgressInfo(info: string): void;
    setBusyCursor(): void;
    setProgressInfo(info: string): void;
    sleep(milliseconds: number): void;
    startBackgroundProgress(info: string, totalSteps: number, isCancellable: boolean): void;
    startProgress(info: string, totalSteps: number, isCancellable: boolean, showTimeElapsed: boolean): void;
    stepBackgroundProgress(numSteps: number): void;
    stepProgress(numSteps: number): void;
    updateBackgroundProgress(position: number): void;
    updateProgress(position: number): void;
    shiftPressed(): boolean;
    ctrlPressed(): boolean;
    getDesktop(): QDesktopWidget;
}

/**
 * Implements a script-able RenderMan interface for the scene to render itself through the 3Delight renderer. See Also: DzRenderMgr :: findRenderer () DzDelightRenderer Sample: Rendering : Scripted Renderer Settings Sample: Rendering : Scripted Renderer Save Preset Sample: Rendering : Scripted Renderer Load Sample: Rendering : Scripted Renderer Pass Attention: This class is only available as a component of DAZ Studio Advanced Edition.
 */
declare class DzScriptedRenderer {
    buildEnvironmentSpaceTransform(): void;
    cameraProject(camera: DzCamera, width: number, height: number): void;
    continueAfterPreProcess(): boolean;
    createLight(light: DzLight, shadowMap: string): void;
    deleteFiles(files: any[]): void;
    doDefaultDisplay(): void;
    doDefaultShadowPass(options: DzRenderOptions, camera: DzCamera, light: DzLight, dir: string, reuse: boolean): string;
    doDefaultShadowPass(options: DzRenderOptions, camera: DzCamera, dir: string, reuse: boolean): any[];
    doDefaultShadowPassEnd(options: DzRenderOptions, camera: DzCamera, light: DzLight): void;
    doDefaultShadowPassPrep(options: DzRenderOptions, camera: DzCamera, light: DzLight, dir: string, reuse: boolean): string;
    doShutter(opts: DzRenderOptions): void;
    fullSceneCameraProject(camera: DzCamera, width: number, height: number): void;
    getDefaultShaderSearchPath(): string;
    getDefinitionFile(): string;
    getDisplacementPreProcessScript(): string;
    getHandler(): DzRenderHandler;
    getLight(index: number): DzLight;
    getLightCount(): number;
    getLightPreProcessScript(): string;
    getLightsToRender(): any[];
    getNode(index: number): DzNode;
    getNodeCount(): number;
    getNodesToRender(): any[];
    getNumIlluminateHandels(): number;
    getPropertyHolder(): DzElement;
    getRenderScript(): string;
    getSurfacePreProcessScript(): string;
    prepareMotionSamples(): void;
    prepareMotionSamples(nodes: any[]): void;
    prepareNodeMotionSamples(node: DzNode): void;
    removeLight(index: number): void;
    removeNode(index: number): void;
    renderBackDrop(backdrop: DzBackdrop, width: number, height: number): void;
    renderNode(node: DzNode): void;
    renderNodes(nodes: any[]): void;
    riAreaLightSource(name: string, tokens: any[], params: any[]): number;
    riAtmosphere(name: string, tokens: any[], params: any[]): void;
    riAttribute(name: string, tokens: any[], params: any[]): void;
    riAttributeBegin(): void;
    riAttributeEnd(): void;
    riBegin(ribPath: string): void;
    riCamera(camera: string, tokens: any[], params: any[]): void;
    riClipping(hither: number, yon: number): void;
    riClippingPlane(x: number, y: number, z: number, nx: number, ny: number, nz: number): void;
    riColor(Cs: { r: number, g: number, b: number, a: number }): void;
    riConcatTransform(transform: DzMatrix4): void;
    riCoordinateSystem(space: string): void;
    riCoordSysTransform(space: string): void;
    riCropWindow(xmin: number, xmax: number, ymin: number, ymax: number): void;
    riDeclare(name: string, declaration: string): void;
    riDepthOfField(fstop: number, focallength: number, focaldistance: number): void;
    riDetailRange(minvis: number, lowtran: number, uptran: number, maxvis: number): void;
    riDisplacement(name: string, tokens: any[], params: any[]): void;
    riDisplay(name: string, type: string, mode: string, tokens: any[], params: any[]): void;
    riDisplayChannel(channel: string, tokens: any[], params: any[]): void;
    riElse(): void;
    riElseIf(expression: string, tokens: any[], params: any[]): void;
    riEndWorld(message: string): void;
    riExposure(gain: number, gamma: number): void;
    riExterior(name: string, tokens: any[], params: any[]): void;
    riFormat(xres: number, yres: number, aspect: number): void;
    riFrameAspectRatio(aspect: number): void;
    riGeometricApproximation(type: string, value: number): void;
    riHider(type: string, tokens: any[], params: any[]): void;
    riIdentity(): void;
    riIfBegin(expression: string, tokens: any[], params: any[]): void;
    riIfEnd(): void;
    riIlluminate(light: number, onOff: boolean): void;
    riImager(name: string, tokens: any[], params: any[]): void;
    riInterior(name: string, tokens: any[], params: any[]): void;
    riLightSource(name: string, tokens: any[], params: any[]): number;
    riMakeBump(pic: string, tex: string, swrap: string, twrap: string, filterType: number, swidth: number, twidth: number, tokens: any[], params: any[]): void;
    riMakeCubeFaceEnvironment(px: string, nx: string, py: string, ny: string, pz: string, nz: string, tex: string, fov: number, filterType: number, swidth: number, twidth: number, tokens: any[], params: any[]): void;
    riMakeLatLongEnvironment(pic: string, tex: string, filterType: number, swidth: number, twidth: number, tokens: any[], params: any[]): void;
    riMakeShadow(pic: string, tex: string, tokens: any[], params: any[]): void;
    riMakeTexture(pic: string, tex: string, swrap: string, twrap: string, filterType: number, swidth: number, twidth: number, tokens: any[], params: any[]): void;
    riMatte(onoff: boolean): void;
    riMultiplyShadingRate(ratemultiplier: number): void;
    riOpacity(Os: { r: number, g: number, b: number, a: number }): void;
    riOption(name: string, tokens: any[], params: any[]): void;
    riOrientation(orientation: string): void;
    riPerspective(fov: number): void;
    riPixelFilter(filterType: number, xwidth: number, ywidth: number): void;
    riPixelSamples(xsamples: number, ysamples: number): void;
    riPixelVariance(variation: number): void;
    riProjection(name: string, tokens: any[], params: any[]): void;
    riQuantize(type: string, one: number, qmin: number, qmax: number, ampl: number): void;
    riRelativeDetail(relativedetail: number): void;
    riReverseOrientation(): void;
    riRotate(angle: number, dx: number, dy: number, dz: number): void;
    riScale(dx: number, dy: number, dz: number): void;
    riScopedCoordinateSystem(space: string): void;
    riScreenWindow(left: number, right: number, bot: number, top: number): void;
    riShader(name: string, handle: string, tokens: any[], params: any[]): void;
    riShadingInterpolation(type: string): void;
    riShadingRate(size: number): void;
    riShutter(smin: number, smax: number): void;
    riSides(nsides: number): void;
    riSkew(angle: number, dx1: number, dy1: number, dz1: number, dx2: number, dy2: number, dz2: number): void;
    riSurface(name: string, tokens: any[], params: any[]): void;
    riTransform(transform: DzMatrix4): void;
    riTransformBegin(): void;
    riTransformEnd(): void;
    riTranslate(dx: number, dy: number, dz: number): void;
    riWorldBegin(): void;
    setBackgroundColor(color: { r: number, g: number, b: number, a: number }): void;
    setCleanUpScript(filename: string): void;
    setContinueAfterPreProcess(shouldContinue: boolean): void;
    setCropWindow(handler: DzRenderHandler): void;
    setDefinitionFile(definitionFile: string): void;
    setDisplacementPreProcessScript(filename: string): void;
    setIsShadowPass(onOff: boolean): void;
    setLightPreProcessScript(filename: string): void;
    setModeBiased(yesNo: boolean): boolean;
    setModeDefaultMaterialClassname(classname: string): boolean;
    setModePhysicallyBased(yesNo: boolean): boolean;
    setModeSupportsAdvancedCamera(yesNo: boolean): boolean;
    setModeSupportsCameraBlades(yesNo: boolean): boolean;
    setRenderScript(filename: string): void;
    setSurfacePreProcessScript(filename: string): void;

    // SIGNALS
    defintionFileChanged(): void;
}

/**
 * A reference counted object ( DzRefCountedItem ) is an object that is intended to be shared between multiple owners - each owner registers an interest in the object when taking ownership, and dereferences the object when it is no longer needed. This mechanism serves to ensure that the referenced object is not deleted while in use and automatically deleted when no longer in use. There are cases, however, where it is desirable to keep one of these objects from being deleted even though it is not referenced by another object in the scene. These cases are where DzScriptHandle becomes useful - its purpose is to provide a mechanism by which a reference counted object is ensured to exist for at least the lifetime of the DzScriptHandle that references it. The lifetime of a DzScriptHandle depends on the scope of the script variable that contains it (e.g., function scope, global scope), but is ultimately limited to the lifetime of the script. Since: 4.15.0.6
 */
declare class DzScriptHandle {
    handle(): any;
    object: any;
    valid: boolean;
}

/**
 * Represents a sorted list of indices - such as a group of vertices, or faces - that is constructable from script. Since: 4.11.0.61
 */
declare class DzScriptIndexList {
    setIndices(list: any[]): void;
}

/**
 * This pane provides users with an Integrated Development Environment (IDE) that is specifically tailored to the development of DAZ Script for use in Daz Studio. It includes several standard features expected in a modern IDE, such as line numbering, syntax highlighting, and code folding. In addition to these core features, the pane allows users to execute a script directly within Daz Studio while the script is being developed, making testing/debugging easier. The Script IDE pane is accessible within the UI via the Window > Panes (Tabs) menu. Triggering the “Script IDE” action will toggle visibility of the pane. As is the case for any pane in the application, this pane can float (be undocked) in its own pane group or be docked with other panes, as desired. The Script IDE pane is accessible through the scripting API using DzPaneMgr :: findPane (). MenuBar and Menus A menubar, with menus and actions that pertain specifically to the IDE, is located at the top of the pane. Many of the actions found here provide access to basic file operations, such as opening, closing, and saving scripts or basic editing operations, such as copy, paste and find/replace. Also found here are actions that provides access to attributes of the script, such as API version and type, as well as preferences that provide control over look, feel and formatting. Script Tabs Multiple script documents can be open within the Script IDE pane at the same time. Script tabs provide access to the individual script documents. Each tab displays the shortname of the file that the script document was loaded from. If the script document was not loaded from a file, the script tab displays “Untitled” for its name. Output Window At the bottom of the pane is an output window that displays error and warning messages when there is an issue with a script that has been executed from within the Script IDE pane. These messages can be helpful for narrowing down the cause of a failure in the script. Also displayed within this window are the results of calls made to Global :: print () and Global :: debug (). Extending the Script IDE Edit Menu The Edit menu, specifically, has the ability to be extended by placing scripts that use the DzScriptTab API to access and/or manipulate the contents of an open script document within specific directories that are known to the application: <application_home>/resources/Script IDE/… <mapped_native_dir>/data/resources/Script IDE/<vendor_name>/<product_name>/… <daz_connect_product>/data/resources/script ide/<vendor_name>/<product_name>/… The folder/file structure that resides within these specific directories is reflected within the middle portion of the Edit menu. Where an adjacent and corresponding PNG exists for a given script within this structure, that PNG will be used for the script action's icon. In the case of relative path collisions. Events There are three specific events that occur in the Script IDE that you have the ability to directly extend the functionality of: When a new script is created: Script IDE: File > New Script When a script document is opened from file Script IDE: File > Open Script… Drag from OS file browser, drop onto Script IDE pane Asset View Context Menu: Open in Script IDE… When a script document is saved to file Script IDE: File > Save Script Script IDE: File > Save Script As… Script IDE: File > Save Encrypted Script… These three events are extended by placing a corresponding script, which use the DzScriptTab API to access and/or manipulate the contents of the invoking script document, within the <application_home>/resources/Script IDE/ directory: _new.dsa _open.dsa _save.dsa Transient Variables When extending the Script IDE pane, the scripts described above provide transient global variables that provide convenient access to key objects: Pane - refers to the Script IDE pane Tab - refers to the DzScriptTab that invoked execution of the script Encryption It is important to understand that while the ability to open and execute encrypted scripts from within the Script IDE pane is provided, the contents of any such script cannot be accessed directly from within the Script IDE pane; placeholder text indicating that the contents of the script is encrypted will be displayed instead. The DzScript object that holds the contents of any loaded script and the DzScriptTab that displays the contents of a script are separate distinct objects.
 */
declare class DzScriptPane {
    closeAllScripts(): boolean;
    closeAllScriptsExceptCurrent(): boolean;
    closeScript(): boolean;
    copySelection(): boolean;
    currentScriptTab(): DzScriptTab;
    currentScriptTabIndex(): number;
    cutSelection(): boolean;
    deleteSelection(): boolean;
    execute(): boolean;
    findFirst(): boolean;
    findNext(): boolean;
    findPrevious(): boolean;
    getFindText(): string;
    getNumScriptTabs(): number;
    getReplaceText(): string;
    getScriptTab(index: number): DzScriptTab;
    gotoLine(line: number): boolean;
    indent(levels: number): boolean;
    indexOf(scriptTab: DzScriptTab): number;
    indexOfFile(filename: string): number;
    isFileOpen(filename: string): boolean;
    isFindMatchCaseChecked(): boolean;
    isFindRegExpChecked(): boolean;
    isFindWholeWordsChecked(): boolean;
    needsSave(): boolean;
    newScript(): void;
    openFile(filename: string): void;
    openScript(): boolean;
    pasteAtCursor(): boolean;
    refreshEditMenu(): void;
    reloadScript(): boolean;
    replaceAll(): boolean;
    replaceNext(): boolean;
    replacePrevious(): boolean;
    saveEncryptedScript(): boolean;
    saveFile(filename: string): boolean;
    saveScript(): boolean;
    saveScriptAs(): boolean;
    selectAll(): boolean;
    setCurrentScriptTab(index: number): void;
    setFindMatchCaseChecked(yesNo: boolean): void;
    setFindRegExpChecked(yesNo: boolean): void;
    setFindText(text: string): void;
    setFindWholeWordsChecked(yesNo: boolean): void;
    setReplaceText(text: string): void;
    showAttributesFrame(onOff: boolean): void;
    showFindReplaceFrame(onOff: boolean): void;
    showPreferences(): boolean;
    unindent(levels: number): boolean;

    // SIGNALS
    attributesToggleChanged(onOff: boolean): void;
    findReplaceToggleChanged(onOff: boolean): void;
}

/**
 * Provides a widget that is used to display and edit a DAZ Script document. Since: 4.11.0.132
 */
declare class DzScriptTab {
    appendText(text: string): boolean;
    beginEdit(): boolean;
    centerCursor(): void;
    clear(): void;
    clearRedoStack(): void;
    clearSelection(): boolean;
    clearUndoRedoStacks(): void;
    clearUndoStack(): void;
    copySelection(): boolean;
    cutSelection(): boolean;
    deleteSelection(): boolean;
    finishEdit(): boolean;
    foldLine(line: number): boolean;
    getCursorAnchor(): number;
    getCursorColumnNumber(): number;
    getCursorLineNumber(): number;
    getCursorPosition(): number;
    getFilename(): string;
    getFilepath(): string;
    getLineText(line: number): string;
    getSelectedText(): string;
    getText(): string;
    getType(): string;
    getVersion(): DzVersion;
    gotoLine(line: number): boolean;
    indent(levels: number): boolean;
    insertText(text: string): boolean;
    isCursorAtEnd(): boolean;
    isCursorAtLineEnd(): boolean;
    isCursorAtLineStart(): boolean;
    isCursorAtStart(): boolean;
    isEncrypted(): boolean;
    isLineFoldable(line: number): boolean;
    isLineFolded(line: number): boolean;
    isModified(): boolean;
    markText(text: string, caseSense: number): void;
    moveCursorPosition(operation: CursorMoveOperation, keepAnchor: boolean, iterations: number): boolean;
    needsSave(): boolean;
    needsSaveAs(): boolean;
    numAvailableRedoSteps(): number;
    numAvailableUndoSteps(): number;
    numCharacters(): number;
    numLines(): number;
    pasteAtCursor(): boolean;
    redo(): void;
    reloadScript(): boolean;
    saveEncryptedScript(): boolean;
    saveScript(): boolean;
    saveScriptAs(): boolean;
    selectAllText(): boolean;
    setCursorPosition(pos: number, keepAnchor: boolean): void;
    setCursorPosition(line: number, column: number, keepAnchor: boolean): void;
    setLineText(line: number, text: string): boolean;
    setText(text: string): boolean;
    setType(type: string): boolean;
    setVersion(version: DzVersion): boolean;
    setVersionBuild(build: number): boolean;
    setVersionMajor(major: number): boolean;
    setVersionMinor(minor: number): boolean;
    setVersionRevision(revision: number): boolean;
    toggleFold(line: number): boolean;
    undo(): void;
    unfoldLine(line: number): boolean;
    unindent(levels: number): boolean;
    updateSidebar(): void;

    // SIGNALS
    blockCountChanged(count: number): void;
    copyAvailable(yesNo: boolean): void;
    cursorPositionChanged(): void;
    modificationChanged(state: boolean): void;
    nameChanged(): void;
    redoAvailable(yesNo: boolean): void;
    selectionChanged(): void;
    textChanged(): void;
    typeChanged(): void;
    undoAvailable(yesNo: boolean): void;
    updateRequest(rect: Rect, dy: number): void;
    versionChanged(): void;
}

/**
 * Provides a scrolling view of another widget. Since: 4.6.2.51
 */
declare class DzScrollArea {
    alignment(): AlignmentFlags;
    maximumViewportSize: Size;
    widgetResizable: boolean;

    ensureVisible(x: number, y: number, xmargin: number, ymargin: number): void;
    ensureWidgetVisible(childWidget: DzWidget, xmargin: number, ymargin: number): void;
    hideFrame(): void;
    setHorizontalScrollbarDisplay(onOff: boolean): void;
    setVerticalScrollbarDisplay(onOff: boolean): void;
    setWidget(widget: DzWidget): void;
}

/**
 * Provides a scrolling area with on-demand scroll bars. Deprecated Exists only to keep old code working. Do not use in new code. Use DzScrollArea where possible instead.
 */
declare class DzScrollView {
}

/**
 * The primary purpose of this container type is to collect results returned by a database query for assets. See Also: DzAssetMgr :: searchFiles () DzAssetMgr :: searchForAssetsByKeywords () DzAssetMgr :: searchForAssets () DzAssetMgr :: searchForAssetsInCategory () DzAssetMgr :: searchForProductAssets () DzAssetMgr :: searchForAssetAddOns () DzAssetMgr :: searchForAssetTargets ()
 */
declare class DzSearchContainer {
    hasMoreSearchResults(): boolean;
}

/**
 * Represents a reference counted list of geometric elements in a mesh that are collected into a group intended for selection. The group is stored as a list of integers, which are indices into the list of the geometric elements this group references. See Also: DzFacetShape Since: 4.6.3.39
 */
declare class DzSelectionGroup {
}

/**
 * This class provides a mapping between the names of the DzFaceGroup objects associated with a DzFacetMesh and the DzNode objects that are likewise associated with that mesh. This mapping plays a part in the mechanism that allows a user to click on different areas of the mesh in the viewport and have that translate to the selection of a node.
 */
declare class DzSelectionMap {
    addPair(faceGroupName: string, node: DzNode, replaceIfExists: boolean): DzError;
    clearAll(): void;
    clearMissingGroups(mesh: DzFacetMesh): void;
    findGroupForNode(node: DzNode): string;
    findNodeForGroup(groupName: string): DzNode;
    findPair(node: DzNode): number;
    findPair(groupName: string): number;
    getNumPairs(): number;
    getPairGroup(index: number): string;
    getPairNode(index: number): DzNode;
    removePair(index: number): DzError;

    // SIGNALS
    mapModified(): void;
    visibilityChanged(): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzSettings {
    clear(): void;
    copySetting(which: number, copyTo: DzSettings): void;
    copySetting(key: string, copyTo: DzSettings): void;
    fromString(settings: string): boolean;
    getBoolValue(key: string, def: boolean): boolean;
    getFloatValue(key: string, def: number): number;
    getIntValue(key: string, def: number): number;
    getKey(which: number): string;
    getNumValues(): number;
    getSettingIndex(key: string): number;
    getSettingsValue(key: string): DzSettings;
    getStringValue(key: string, def: string): string;
    getValue(which: number): string;
    getValueType(which: number): Type;
    hasKey(key: string): number;
    removeValue(key: string): void;
    replaceWithSettings(settings: DzSettings): void;
    setBoolValue(key: string, value: boolean): void;
    setFloatValue(key: string, value: number): void;
    setIntValue(key: string, value: number): void;
    setSettingsValue(key: string, settings: DzSettings): DzSettings;
    setSettingsValue(key: string): DzSettings;
    setStringValue(key: string, value: string): void;
    toJson(): any;
    toJsonString(): string;
    toScript(varName: string, script: DzScript, indent: number, define: boolean): void;
    toString(): string;
}

/**
 * Choosing the appropriate key type and pushing/popping keys (paths) is handled by the object.
 */
declare class DzSettingsHelper {
    get(path: string, name: string, value: any): any;
    hasValue(path: string, name: string): boolean;
    removeValue(path: string, name: string): boolean;
    set(path: string, name: string, value: any): void;
}

/**
 * An asset save filter for saving a Shader Preset in the DSON format. See Also: Sample: Save a Shader Preset
 */
declare class DzShaderAssetFilter {
}

/**
 * DzShaderBricks encapsulate the creation of shaders from the brick connection network seen in the Shader Mixer pane.
 */
declare class DzShaderBrick {
}

/**
 * This class provides a DzBasicCamera derived object with creator-defined properties that will be passed to the RSL Shader at render-time. Properties intended to be used to pass values as arguments to a shader attached to the camera must be added using DzRSLShader . Properties for the camera that will be used by the render-time scripts to set attributes must be added via DzElement :: addProperty ().
 */
declare class DzShaderCamera {
    addShader(shader: DzRSLShader): boolean;
    getCameraName(): string;
    getDefinitionFile(): string;
    getNumShaders(): number;
    getRenderTimeFile(): string;
    getShader(index: number): DzRSLShader;
    removeShader(shader: DzRSLShader): boolean;
    setCameraName(name: string): void;
    setDefinitionFile(definitionFile: string, doOverride: boolean, runScript: boolean): void;
    setRenderTimeFile(renderTimeFile: string): boolean;
    declare(tokens: any[], types: any[]): void;
    setDisplay(name: string, type: string, mode: string, tokens: any[], params: any[]): void;
    setHider(type: string, tokens: any[], params: any[]): void;
    setOption(option: string, tokens: any[], params: any[]): void;
}

/**
 * DzShaderDescription contains information about a RenderMan shader - this includes the type of the shader, and a list of its parameters.
 */
declare class DzShaderDescription {
    type(): DzShaderType;

    getNumParameters(): number;
    getParameter(i: number): DzShaderParameter;
}

/**
 * This class provides a DzLight derived object with creator-defined properties that will be passed to the RSL Shader at render-time. By default, the light only has two properties - Color and Intensity. The values of these properties are not sent to the shader by default, nor are any attributes set representing the value of these properties. Unless put to use via DzRSLShader , these properties are purely for OpenGL purposes. These properties are not mappable by default, but can be made so by using DzRSLShader :: addMapProperty () or DzRSLShader :: addMappableProperty (). All other properties for the light must be added using DzRSLShader in order to be used to pass values as arguments to the shader. Properties for the light that will be used by the render-time scripts to set attributes must be added via DzElement :: addProperty ().
 */
declare class DzShaderLight {
    addShader(shader: DzRSLShader): boolean;
    getColorControl(): DzColorProperty;
    getDefinitionFile(): string;
    getIntensity(): number;
    getIntensityControl(): DzFloatProperty;
    getLightName(): string;
    getLightType(): LightType;
    getNumShaders(): number;
    getShader(index: number): DzRSLShader;
    getShadowMapPath(): string;
    removeShader(shader: DzRSLShader): boolean;
    setDefinitionFile(definitionFile: string, doOverride: boolean, runScript: boolean): void;
    setLightName(name: string): void;
    setLightType(type: LightType): void;
    setUseLocalShaderSpace(onOff: boolean): void;
    usesLocalShaderSpace(): boolean;
}

/**
 * This class provides a DzMaterial derived object with creator-defined properties that will be passed to the RSL Shader at render-time. By default, the material only has two properties - Diffuse Color (Cs) and Opacity Strength (Os) - which are not passed as tokens to the shader, rather they are attributes sent directly to the renderer, via RiColor() and RiOpacity() respectively. These properties are not mappable by default, but can be made so by using DzRSLShader :: addMapProperty (). All other properties for the material must be added using DzRSLShader :: addShaderProperty () and DzRSLShader :: addMappableProperty () in order to be used to pass values as arguments to the shader. Properties for the material that will be used by the render-time scripts to set attributes must be added via DzElement :: addProperty (). Samples: rispec_constant_shader_preset - A [heavily commented] Shader Preset that applies a material definition script (below) for the standard RenderMan Constant Surface Shader. See Also: rispec_constant_shader_definition - The definition file for the standard RenderMan Constant Surface Shader, that builds the properties displayed to users in the Surfaces tab (Advanced sub tab). rispec_constant_material_definition - The definition file for the above, that builds the shader objects used by the render for the current material. rispec_constant_surface_shader - The RSL source for the standard RenderMan Constant Surface Shader. s_standard_render_time_script - The render-time script that sets various RiAttributes dependant on the values of properties provided to the user.
 */
declare class DzShaderMaterial {
    addShader(shader: DzRSLShader): boolean;
    getDefinitionFile(): string;
    getDiffuseProperty(): DzColorProperty;
    getNumShaders(): number;
    getOpacityProperty(): DzFloatProperty;
    getShader(index: number): DzRSLShader;
    removeShader(shader: DzRSLShader): boolean;
    setDefinitionFile(definitionFile: string, doOverride: boolean, runScript: boolean): void;
    setMaterialName(name: string): void;
    setNeedsTangentSpaceParams(onoff: boolean): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzShaderParameter {
    type(): DzShaderParamType;
}

/**
 * An asset save filter for saving a Shader Definition Support Asset in the DSON format. See Also: Sample: Save a Shader Definition Support Asset
 */
declare class DzShaderSupportAssetFilter {
}

/**
 * A container class that references a DzGeometry and holds all the pertinent material definitions, etc for that geometry.
 */
declare class DzShape {
    getCurrentShapeForNode(node: DzNode): DzShape;
    addMaterial(mat: DzMaterial): DzError;
    clearMaterialSelection(): void;
    createMaterial(name: string): DzError;
    findMaterial(materialName: string): DzMaterial;
    findMaterialIndex(materialName: string): number;
    findMaterialIndex(mat: DzMaterial): number;
    findMaterials(materialName: string): any[];
    getAllMaterials(): any[];
    getAllRenderPrioritizedMaterials(): any[];
    getAllSelectedMaterials(): any[];
    getAssemblyGeometry(): DzGeometry;
    getCurrentGeometry(type: GeometryType): DzGeometry;
    getGeometry(): DzGeometry;
    getMaterial(which: number): DzMaterial;
    getModifiableAssemblyGeom(isRender: boolean): DzVertexMesh;
    getNode(): DzNode;
    getNumMaterials(): number;
    getSelectedMaterial(which: number): DzMaterial;
    hasAssemblyGeometry(): boolean;
    hasDifferentRenderThanDraw(): boolean;
    insertMaterial(mat: DzMaterial, index: number): DzError;
    removeMaterial(mat: DzMaterial): DzError;
    removeMaterialByName(materialName: string, defaultName: string): DzError;
    replaceMaterial(currentMat: DzMaterial, newMat: DzMaterial): DzError;

    // SIGNALS
    aboutToFinalize(mesh: DzVertexMesh): void;
    aboutToReplaceMaterial(currentMat: DzMaterial, newMat: DzMaterial): void;
    assemblyChanged(): void;
    assemblyNeedsConfigurationCheck(): void;
    geomChanged(): void;
    materialAdded(mat: DzMaterial): void;
    materialChanged(): void;
    materialListChanged(): void;
    materialRemoved(mat: DzMaterial): void;
    materialReplaced(oldMat: DzMaterial, newMat: DzMaterial): void;
    materialSelected(mat: DzMaterial): void;
    materialSelectionChanged(): void;
    materialUnselected(mat: DzMaterial): void;
    smoothingChanged(): void;
    subdivisonChanged(): void;
    uvsChanged(): void;
    vertexSelectionChanged(): void;
}

/**
 * See Also: Sample: Adjust Rigging to Shape Attention: This object is provided by the Joint Editor Tool plugin. It is only available when the Joint Editor Tool plugin is activated and enabled. Since: 4.9.3.93
 */
declare class DzShapeRiggingAdjuster {
    doAdjustments(): boolean;
    setAdjustCenterPoints(yesNo: boolean): void;
    setAdjustEndPoints(yesNo: boolean): void;
    setAdjustFollowTarget(yesNo: boolean): void;
    setAdjustOrientation(yesNo: boolean): void;
    setExcludedBones(boneNames: any[]): void;
    setExcludedFacetGroups(groupNames: any[]): void;
    setFigure(figure: DzFigure): void;
}

/**
 * An asset save filter for saving a Shaping Preset in the DSON format. See Also: Sample: Save a Shaping Preset
 */
declare class DzShapingAssetFilter {
}

/**
 * Implements a custom data item that allows arbitrary data to be associated with an element of the scene. See Also: DzElement :: addDataItem () DzElement :: removeDataItem () DzElement :: deleteDataItem () DzElement :: getNumDataItems () DzElement :: getDataItem () DzElement :: getDataItemList () DzElement :: getUniqueDataItemName () DzElement :: findDataItem () DzElement :: moveDataItemToIndex () DzElement :: findDataItemIndex ()
 */
declare class DzSimpleElementData {
    getSettings(): DzSettings;
}

/**
 * Implements a custom data item that causes a specified script to be executed after the element that owns this data item has been loaded into the scene. A global transient variable named DataItem , which refers to the DzSimpleElementScriptData that invoked the execution of the script, is provided to the script in the global context at runtime. Attempts to use this global variable outside of the associated script will result in a ReferenceError . A global transient variable named FileIOSettings , which refers to the DzFileIOSettings that was used when the element that owns this data item was loaded, is provided to the script in the global context at runtime. Attempts to use this global variable outside of the associated script will result in a ReferenceError . (since 4.9.4.109) If the DzSettings for this data item contains a boolean setting named RunOnce set to true , the specified script will be run once and then this data item will be deleted from the element. Attention: The differences between this implementation and DzElementPostLoadFileData are that this implementation must reference the file path of a script and has an associated DzSettings that can be used to configure the script. See Also: DzElement :: addDataItem () DzElement :: removeDataItem () DzElement :: deleteDataItem () DzElement :: getNumDataItems () DzElement :: getDataItem () DzElement :: getDataItemList () DzElement :: getUniqueDataItemName () DzElement :: findDataItem () DzElement :: moveDataItemToIndex () DzElement :: findDataItemIndex ()
 */
declare class DzSimpleElementScriptData {
    getScriptFilePath(): string;
    setScriptFilePath(script: string): void;
}

/**
 * Implements a custom data item that allows arbitrary data to be associated with the scene. See Also: DzScene :: addDataItem () DzScene :: removeDataItem () DzScene :: getUniqueDataItemName () DzScene :: findDataItem () DzScene :: getNumDataItems () DzScene :: getDataItem () DzScene :: getDataItemList ()
 */
declare class DzSimpleSceneData {
    getSettings(): DzSettings;
}

/**
 * Implements a custom data item that causes a specified script to be executed after the scene has been loaded. A global transient variable named DataItem , which refers to the DzSimpleSceneScriptData that invoked the execution of the script, is provided to the script in the global context at runtime. Attempts to use this global variable outside of the associated script will result in a ReferenceError . A global transient variable named FileIOSettings , which refers to the DzFileIOSettings that was used when the scene was loaded, is provided to the script in the global context at runtime. Attempts to use this global variable outside of the associated script will result in a ReferenceError . (since 4.9.4.109) If the DzSettings for this data item contains a boolean setting named RunOnce set to true , the specified script will be run once and then this data item will be deleted from the scene. See Also: DzScene :: addDataItem () DzScene :: removeDataItem () DzScene :: getUniqueDataItemName () DzScene :: findDataItem () DzScene :: getNumDataItems () DzScene :: getDataItem () DzScene :: getDataItemList ()
 */
declare class DzSimpleSceneScriptData {
    getScriptFilePath(): string;
    setScriptFilePath(script: string): void;
}

/**
 * Implements a simulation engine. Since: 4.9.4.1
 */
declare class DzSimulationEngine {
    clearSimulation(): DzError;
    customSimulate(nodes: any[]): DzError;
    getSimulationElements(list: any[]): any[];
    simulate(): DzError;

    // SIGNALS
    aboutToSimulate(engine: DzSimulationEngine): void;
    simulateFinished(engine: DzSimulationEngine): void;
    simulationError(errorMsg: string): void;
}

/**
 * Responsible for the management of simulation engines, and more generally the process of performing a simulation. There is only one instance of this manager in an application. This instance is created and owned by DzApp . Request the instance via DzApp :: getSimulationMgr (). See Also: Global :: App Sample: Simulate Selected Group Since: 4.9.4.1
 */
declare class DzSimulationMgr {
    clearSimulation(): DzError;
    findSimulationEngine(className: string): DzSimulationEngine;
    getActiveSimulationEngine(): DzSimulationEngine;
    getNumSimulationEngines(): number;
    getSimulationEngine(which: number): DzSimulationEngine;
    getSimulationEngineList(): any[];
    isSimulating(): boolean;
    setActiveSimulationEngine(engine: DzSimulationEngine): void;
    simulate(): DzError;

    // SIGNALS
    activeSimulationEngineChanged(engine: DzSimulationEngine): void;
    simulationEngineAdded(engine: DzSimulationEngine): void;
    simulationError(errorMsg: string): void;
    simulationFinished(succeeded: boolean): void;
    simulationOptionDefaultsRestored(): void;
    simulationStarting(): void;
}

/**
 * An asset save filter for saving a Simulation Settings Preset in the DSON format. See Also: Sample: Save a Simulation Settings Preset
 */
declare class DzSimulationSettingsAssetFilter {
}

/**
 * Since: 4.9.3.135
 */
declare class DzSimulationSettingsProvider {
    assetAuthor(): DzAuthor;
    assetFileRevision: DzVersion;
    assetId: string;
    assetModifiedDate: Date;
    assetNeedSave: boolean;
    assetSource: DzUri;
    assetUri: DzUri;

    duplicateProvider(context: DzElementDuplicateContext): DzSimulationSettingsProvider;
    getShape(): DzShape;
    modifyAsset(newUri: DzUri): boolean;
    modifyAsset(): boolean;
    shouldAlwaysEmbed(): boolean;

    // SIGNALS
    assetModified(): void;
    assetWasSaved(): void;
    settingsChanged(): void;
    shapeChanged(newShape: DzShape, oldShape: DzShape): void;
}

/**
 * This is the script counterpart to the QSize type used in the C++ SDK. A Size object is a two dimensional representation of a width and height. Attention: Inheritance will change to Object in a pending update.
 */
declare class Size {
    height(): number;
    width: number;

    boundedTo(size: Size): Size;
    expandedTo(size: Size): Size;
    isEmpty(): boolean;
    isNull(): boolean;
    isValid(): boolean;
    scale(size: Size, mode: number): void;
    scale(width: number, height: number, mode: number): void;
    transpose(): void;
    translate(): void;
}

/**
 * A specialization of DzNode that owns and manages a hierarchical collection of DzBone instances that form the framework, or skeletal frame, of an object that can be articulated. A skeleton can be autonomous, can be the target of other skeletons that mimic/follow it (i.e., a “follow target”), or can be configured to mimic/follow another skeleton (i.e., a “follower”). See Also: DzBone
 */
declare class DzSkeleton {
    convertFigureToProp(skeleton: DzSkeleton, nodeName: string): DzNode;
    clearGeneratedMorphs(): void;
    findBone(name: string): DzBone;
    findBoneByLabel(label: string): DzBone;
    getAllBones(): any[];
    getDrawGLBones(): boolean;
    getDrawGLBonesControl(): DzBoolProperty;
    getFigureIDControl(): DzFloatProperty;
    getFollowControl(): DzSkeletonProperty;
    getFollowingProjectionOptions(): DzFollowingProjectionOptions;
    getFollowMode(): FollowMode;
    getFollowModeControl(): DzEnumProperty;
    getFollowSkeleton(which: number): DzSkeleton;
    getFollowTarget(): DzSkeleton;
    getGLBonesColorControl(): DzColorProperty;
    getGLBonesEdgeOpacityControl(): DzFloatProperty;
    getGLBonesEdgeStyleControl(): DzEnumProperty;
    getGLBonesFillOpacityControl(): DzFloatProperty;
    getNumFollowSkeletons(): number;
    getUniqueBoneLabel(label: string, bone: DzBone): string;
    getUniqueBoneName(name: string, bone: DzBone): string;
    invalidateBoundingBoxes(checkSkeleton: boolean): void;
    setDrawGLBones(onOff: boolean): void;
    setFollowTarget(skeleton: DzSkeleton): void;

    // SIGNALS
    followTargetChanged(skeleton: DzSkeleton): void;
}

/**
 * A specialized subclass of DzNodeProperty which will only allow the user to select nodes that are skeletons from the scene. This is currently used by skeletons for the 'Fit To' property.
 */
declare class DzSkeletonProperty {
    getSkeletonValue(): DzSkeleton;

    // SIGNALS
    aboutToChange(): void;
}

/**
 * A specialization of DzModifier that provides access to and manages weight-maps associated with mesh binding. Implements industry standard weight-mapped mesh binding techniques, such as Linear Blending Skinning (LBS) and Dual Quaternion Skinning (DQS), as well as a proprietary technique referred to as “TriAx”. (see BindingMode ) This class is not intended to be constructed directly, rather it is created automatically by DzFigure . Create (or retrieve) an instance of DzFigure populated with a DzFacetMesh derived geometry and request its skin-binding via DzFigure :: getSkinBinding (), or use one of the convenience function: findSkin (), findSkinFromNode (), findSkinFromObject (). See Also: DzBoneBinding
 */
declare class DzSkinBinding {
    assetAuthor(): DzAuthor;
    assetFileRevision: DzVersion;
    assetId: string;
    assetModifiedDate: Date;
    assetNeedSave: boolean;
    assetSource: DzUri;
    assetUri: DzUri;
}

/**
 * An abstract base class for widgets that allow the user to adjust a value using a (horizontally oriented) slider. Since: 4.22.1.178
 */
declare class DzSlider {
    clamped(): boolean;
    fullLengthEdit: boolean;
    isEditing: boolean;
    label: string;
    labelVisible: boolean;
    restorable: boolean;
    sensitivity: number;
    text: string;
    textEditable: boolean;
    textVisible: boolean;

    step(positive: boolean): void;

    // SIGNALS
    editCancelled(): void;
    editEnd(): void;
    editStart(): void;
}

/**
 * Implements a custom data item that stores the source of an imported object on the element. Primarily used by the framework to store source paths for imported Poser format content. Can be used as follows to retrieve the path of the CR2 file from which a figure was loaded: Could also be used by plug-in developers for other custom importers to store the source file for imported objects.
 */
declare class DzSourceFileData {
    sourceFilePath(): string;

    getGeometryChanged(): boolean;
    getPoserRuntimeRelativePath(): string;
    setGeometryChanged(onoff: boolean): void;
}

/**
 * Provides the user with the ability to control the size of child widgets by dragging the boundary between the children. See Also: DzDynamicDividerWgt
 */
declare class DzSplitter {
    childrenCollapsible(): boolean;
    handleWidth: number;
    opaqueResize: boolean;
    orientation: Orientation;

    addWidget(widget: DzWidget): void;
    count(): number;
    indexOf(widget: DzWidget): number;
    insertWidget(index: number, widget: DzWidget): void;
    isCollapsible(index: number): boolean;
    restoreState(state: ByteArray): boolean;
    saveState(): ByteArray;
    setCollapsible(index: number, collapse: boolean): void;
    setStretchFactor(index: number, stretch: number): void;
    widget(index: number): DzWidget;
}

/**
 * TODO: Add detailed description.
 */
declare class DzSpotLight {
    getBaseOpacity(): number;
    getBaseOpacityControl(): DzFloatProperty;
    getBeamDistribution(): number;
    getBeamDistributionControl(): DzFloatProperty;
    getDecay(): number;
    getDecayControl(): DzFloatProperty;
    getDisplayPersistence(): boolean;
    getDisplayPersistenceControl(): DzBoolProperty;
    getEdgeOpacity(): number;
    getEdgeOpacityControl(): DzFloatProperty;
    getFalloffDistance(lightPercent: number): number;
    getLightExponent(): number;
    getLightExponentControl(): DzFloatProperty;
    getLightVisibility(): boolean;
    getLineOpacity(): number;
    getOpacityScale(): number;
    getOpacityScaleControl(): DzFloatProperty;
    getRayLength(): number;
    getRayLengthControl(): DzFloatProperty;
    getRayOpacity(): number;
    getRayOpacityControl(): DzFloatProperty;
    getShowBase(): boolean;
    getShowBaseControl(): DzBoolProperty;
    getShowEdge(): boolean;
    getShowEdgeControl(): DzBoolProperty;
    getSpreadAngle(): number;
    getSpreadAngleControl(): DzFloatProperty;
    setBaseOpacity(opacity: number): void;
    setBeamDistribution(distribution: number): void;
    setDecay(decay: number): void;
    setDisplayPersistence(persistence: boolean): void;
    setEdgeOpacity(opacity: number): void;
    setLightExponent(exponent: number): void;
    setOpacityScale(scale: number): void;
    setRayLength(length: number): void;
    setRayOpacity(opacity: number): void;
    setShowBase(yesNo: boolean): void;
    setShowEdge(yesNo: boolean): void;
    setSpreadAngle(spreadAngle: number): void;
}

/**
 * Base class for raw data items that can be archived in the deprecated .daz file format. Instances of this class can be shared between multiple container classes to avoid duplication of large data sets in memory.
 */
declare class DzStorable {
}

/**
 * This is the script counterpart to the QString type used in the C++ SDK. A string is a sequence of zero or more Unicode characters. All string indexes are zero-based, which means the index for the last character in the string sText is always sText.length - 1 . Example: Strings creation and concatenation See Also: DzStringHelper
 */
declare class String {
    length(): number;

    fromCharCode(charCode1: number, ...args: any[]): string;
    charAt(pos: number): string;
    charCodeAt(pos: number): number;
    concat(string1: string, ...args: any[]): string;
    indexOf(pattern: string, startPos: number): number;
    indexOf(pattern: RegExp, startPos: number): number;
    lastIndexOf(pattern: RegExp, startPos: number): number;
    lastIndexOf(pattern: string, startPos: number): number;
    localeCompare(that: string): number;
    match(pattern: RegExp): any[];
    replace(pattern: string, callbackfn: Function): string;
    replace(pattern: RegExp, newValue: string): string;
    replace(pattern: RegExp, callbackfn: Function): string;
    replace(pattern: string, newValue: string): string;
    search(pattern: string): number;
    search(pattern: RegExp): number;
    slice(start: number, end: number): string;
    split(separator: RegExp, limit: number): any[];
    split(separator: string): any[];
    split(pattern: string): any[];
    split(pattern: RegExp): any[];
    split(separator: string, limit: number): any[];
    substring(start: number, end: number): string;
    toLocaleLowerCase(): string;
    toLocaleUpperCase(): string;
    toLowerCase(): string;
    toString(): string;
    toUpperCase(): string;
    trim(): string;
    valueOf(): string;
    arg(value: string, fieldWidth: number): string;
    arg(value: number, fieldWidth: number): string;
    argDec(value: number, fieldWidth: number, format: number, precision: number): string;
    argInt(value: number, fieldWidth: number, base: number): string;
    endsWith(pattern: string): boolean;
    endsWith(pattern: RegExp): boolean;
    find(pattern: RegExp, startPos: number): number;
    find(pattern: string, startPos: number): number;
    findRev(pattern: RegExp, startPos: number): number;
    findRev(pattern: string, startPos: number): number;
    isEmpty(): boolean;
    left(num: number): string;
    lower(): string;
    mid(startIndex: number, num: number): string;
    right(num: number): string;
    searchRev(pattern: RegExp): number;
    searchRev(pattern: string): number;
    startsWith(pattern: RegExp): boolean;
    startsWith(pattern: string): boolean;
    upper(): string;
}

/**
 * TODO: Add detailed description.
 */
declare class DzStringHelper {
    changeSpecialChars(text: string, chars: string): string;
    getMatches(text: string, expression: string): any[];
    getWords(text: string, removeEmpties: boolean): any[];
    indentString(text: string, level: number): string;
    prependCharsIfNumeric(text: string, chars: string): string;
    replaceAll(source: string, findText: string, replaceText: string): string;
    stripCRLF(text: string): string;
    stripSpaces(text: string): string;
}

/**
 * TODO: Add detailed description.
 */
declare class DzStringProperty {
    getDefaultValue(): string;
    getValue(): string;
    setDefaultValue(val: string): boolean;
    setValue(val: string): boolean;
}

/**
 * Interface Colors User-customizable interface colors for the current style. See findInterfaceColor (), getNumInterfaceColors (), getInterfaceColorName (), getInterfaceColorDescription (), getInterfaceColor (), getInterfaceColor (), getInterfaceColorDefault (), getInterfaceColorDisplaySettings (), setInterfaceColor () Interface Numbers User-customizable interface numbers for the current style. See findInterfaceNumber (), getNumInterfaceNumbers (), getInterfaceNumberName (), getInterfaceNumberDescription (), getInterfaceNumber (), getInterfaceNumberDefault (), getInterfaceNumberDisplaySettings (), setInterfaceNumber () Text Styles All text styles are added by the application; the Qt framework does not provide text styles. See getNumTextStyles (), getTextStyleName (), findTextStyle (), textStyle (), textStyleColor () Pixel Metrics All pixel metrics that are NOT prefixed with a “DZ_” are wrappers for QStyle::PixelMetric provided by the Qt framework. All pixel metrics that ARE prefixed with a “DZ_” are added by the application. See getNumPixelMetrics (), getPixelMetricName (), findPixelMetric (), pixelMetric () Style Hints All style hints that are NOT prefixed with a “DZ_” are wrappers for QStyle::StyleHint provided by the Qt framework. All style hints that ARE prefixed with a “DZ_” are added by the application. See getNumStyleHints (), getStyleHintName (), findStyleHint(() Standard Pixmaps All standard pixmaps that are NOT prefixed with a “DZ_” are wrappers for QStyle::StandardPixmap provided by the Qt framework. All standard pixmaps that ARE prefixed with a “DZ_” are added by the application. See getNumStandardPixmaps (), getStandardPixmapName (), findStandardPixmap (), standardPixmap () Primitive Elements All primitive elements that are NOT prefixed with a “DZ_” are wrappers for QStyle::PrimitiveElement provided by the Qt framework. All primitive elements that ARE prefixed with a “DZ_” are added by the application. See getNumPrimitiveElements (), getPrimitiveElementName (), findPrimitiveElement () Action Icons See actionPixmap () The action index is constantly evolving - below is a script that can be run to get a list of all available actions Example: Reset the current style colors to their default values.
 */
declare class DzStyle {
    compileStyleDefinition(infile: string, outfile: string): DzError;
    findPixelMetric(name: string): number;
    findPrimitiveElement(name: string): number;
    findStandardPixmap(name: string): number;
    findStyleHint(name: string): number;
    findTextStyle(name: string): number;
    getNumPixelMetrics(): number;
    getNumPrimitiveElements(): number;
    getNumStandardPixmaps(): number;
    getNumStyleHints(): number;
    getNumTextStyles(): number;
    getPixelMetricName(which: number): string;
    getPrimitiveElementName(which: number): string;
    getStandardPixmapName(which: number): string;
    getStyleHintName(which: number): string;
    getTextStyleName(which: number): string;
    actionPixmap(className: string, mode: PixmapMode, state: PixmapState): Pixmap;
    findInterfaceColor(name: string): number;
    findInterfaceNumber(name: string): number;
    getInterfaceColor(name: string): { r: number, g: number, b: number, a: number };
    getInterfaceColor(which: number): { r: number, g: number, b: number, a: number };
    getInterfaceColorDefault(which: number): { r: number, g: number, b: number, a: number };
    getInterfaceColorDescription(which: number): string;
    getInterfaceColorDisplaySettings(which: number, settings: DzSettings): void;
    getInterfaceColorName(which: number): string;
    getInterfaceNumber(name: string, defaultValue: number): number;
    getInterfaceNumber(which: number): number;
    getInterfaceNumberDefault(which: number): number;
    getInterfaceNumberDescription(which: number): string;
    getInterfaceNumberDisplaySettings(which: number, settings: DzSettings): void;
    getInterfaceNumberName(which: number): string;
    getNumInterfaceColors(): number;
    getNumInterfaceNumbers(): number;
    getStyleDefinition(): string;
    pixelMetric(metricName: string): number;
    setInterfaceColor(which: number, color: { r: number, g: number, b: number, a: number }): void;
    setInterfaceNumber(which: number, value: number): void;
    setStyledIcon(button: QAbstractButton, pixmapName: string): boolean;
    standardPixmap(pixmapName: string): Pixmap;
    textStyle(styleName: string): Font;
    textStyleColor(styleName: string): { r: number, g: number, b: number, a: number };

    // SIGNALS
    interfaceColorsChanged(): void;
    interfaceNumbersChanged(): void;
}

/**
 * Deprecated Exists only to keep code written prior to 4.6.2.23 working. Do not use in new code. Use DzTextureLayer :: BlendSubtract instead.
 */
declare class DzSubtractBlend {
}

/**
 * This error is thrown by the interpreter to indicate that a parsing error has occurred. See the ECMA script specification for more information.
 */
declare class SyntaxError {
}

/**
 * This object provides functions to access and manipulate environment variables. It is accessible via the Global :: System variable.
 */
declare class DzSystem {
    getenv(environmentVariable: string): string;
    setenv(environmentVariable: string, value: string): void;
    print(expression: string): void;
    println(expression: string): void;
}

/**
 * Provides a stack of tabbed widgets.
 */
declare class DzTabWidget {
    count(): number;
    currentIndex: number;
    documentMode: boolean;
    movable: boolean;
    tabPosition: TabPosition;
    tabsClosable: boolean;
    usesScrollButtons: boolean;

    addTab(page: DzWidget, label: string): number;
    clear(): void;
    cornerWidget(): DzWidget;
    currentWidget(): DzWidget;
    indexOf(page: DzWidget): number;
    insertTab(index: number, page: DzWidget, label: string): number;
    isTabEnabled(index: number): bool;
    removeTab(index: number): void;
    setCornerWidget(widget: DzWidget): void;
    setCurrentWidget(page: DzWidget): void;
    setTabEnabled(index: number, enable: boolean): void;
    setTabText(index: number, label: string): void;
    setTabToolTip(index: number, tip: string): void;
    setTabWhatsThis(index: number, text: string): void;
    tabText(index: number): string;
    tabToolTip(index: number): string;
    tabWhatsThis(index: number): string;
    widget(index: number): DzWidget;

    // SIGNALS
    currentChanged(index: number): void;
    tabCloseRequested(index: number): void;
}

/**
 * Extends DzTextEdit (in read-only mode), adding functionality that allows users to navigate hyper-linked documents.
 */
declare class DzTextBrowser {
    backwardCount(): number;
    forwardCount: number;
    isBackwardAvailable: boolean;
    isForwardAvailable: boolean;
    openExternalLinks: boolean;
    openLinks: boolean;
    searchPaths: any[];
    source: string;

    backward(): void;
    clearHistory(): void;
    forward(): void;
    historyTitle(index: number): string;
    historyUrl(index: number): string;
    home(): void;
    reload(): void;

    // SIGNALS
    anchorClicked(name: string, link: string): void;
    backwardAvailable(available: boolean): void;
    forwardAvailable(available: boolean): void;
    highlighted(link: string): void;
    historyChanged(): void;
    linkClicked(link: string): void;
    sourceChanged(src: string): void;
}

/**
 * Provides a powerful single-page rich text editor widget.
 */
declare class DzTextEdit {
    acceptRichText(): boolean;
    autoFormatting: AutoFormattingFlag;
    blockCount: number;
    bold: boolean;
    characterCount: number;
    cursorWidth: number;
    documentTitle: string;
    family: string;
    font: Font;
    html: string;
    italic: boolean;
    lineCount: number;
    lineWrapColumnOrWidth: number;
    lineWrapMode: LineWrapMode;
    modified: boolean;
    overwriteMode: boolean;
    plainText: string;
    pointSize: number;
    readOnly: boolean;
    redoAvailable: boolean;
    selectedText: string;
    tabChangesFocus: boolean;
    tabStopWidth: number;
    text: string;
    textBackgroundColor: { r: number, g: number, b: number, a: number };
    textColor: { r: number, g: number, b: number, a: number };
    textInteractionFlags: TextInteractionFlags;
    underline: boolean;
    undoAvailable: boolean;
    undoRedoEnabled: boolean;
    weight: number;
    wordWrapMode: WrapMode;

    anchorAt(pos: Point): string;
    append(text: string): void;
    backspace(): void;
    backspaceWord(): void;
    clear(): void;
    copy(): void;
    cursorBackward(mark: boolean, steps: number): void;
    cursorForward(mark: boolean, steps: number): void;
    cursorWordBackward(mark: boolean, steps: number): void;
    cursorWordForward(mark: boolean, steps: number): void;
    cut(): void;
    del(): void;
    deleteWord(): void;
    down(mark: boolean, steps: number): void;
    end(mark: boolean): void;
    ensureCursorVisible(): void;
    find(expression: string, caseSensitive: boolean, wholeWord: boolean, backward: boolean): boolean;
    hasSelectedText(): boolean;
    home(mark: boolean): void;
    insertBlock(): void;
    insertHtml(text: string): void;
    insertPlainText(text: string): void;
    lineEnd(mark: boolean): void;
    lineStart(mark: boolean): void;
    pageDown(mark: boolean): void;
    pageUp(mark: boolean): void;
    paste(): void;
    redo(): void;
    scrollToAnchor(name: string): void;
    selectAll(): void;
    selectedText(): string;
    selectionEnd(): number;
    selectionStart(): number;
    text(blockIdx: number): string;
    undo(): void;
    up(mark: boolean, steps: number): void;
    zoomIn(range: number): void;
    zoomOut(range: number): void;

    // SIGNALS
    copyAvailable(yesNo: boolean): void;
    cursorPositionChanged(): void;
    redoAvailable(yesNo: boolean): void;
    selectionChanged(): void;
    textChanged(): void;
    undoAvailable(yesNo: boolean): void;
}

/**
 * This class is not intended to be constructed directly. Create (or retrieve) an instance from DzImageMgr - this ensures that there is only one instance of a given image in memory at a time, and also ensures that necessary conversions for rendering the image occurs correctly.
 */
declare class DzTexture {
    getFilename(): string;
    getGamma(): number;
    getGLAlphaTextureSize(): Size;
    getGLTextureSize(): Size;
    getOriginalImageSize(): Size;
    getPreviewPixmap(size: Size): Pixmap;
    getPreviewPixmap(width: number, height: number): Pixmap;
    getRevision(): number;
    getTempFilename(): string;
    getTextureType(): number;
    incrementRevision(emitDataChanged: boolean): void;
    loadImageData(image: Image): boolean;
    refresh(): void;
    setGamma(gamma: number): void;
    setTextureType(val: number): void;

    // SIGNALS
    drawnDataChanged(): void;
    tempFilenameChanged(filename: string): void;
}

/**
 * See Also: DzLayeredTexture .
 */
declare class DzTextureComponent {
    color(): { r: number, g: number, b: number, a: number };
    enabled: boolean;
    flippedHorizontal: boolean;
    flippedVertical: boolean;
    imageFile: string;
    invert: boolean;
    label: string;
    offset: Point;
    opacity: number;
    rotation: Rotation;
    xOffset: number;
    xScale: number;
    yOffset: number;
    yScale: number;

    copyFrom(comp: DzTextureComponent): void;
    flip(horizontal: boolean, vertical: boolean): void;
    loadImageData(image: Image): boolean;
    needsImageRefresh(): boolean;
    setScale(xScale: number, yScale: number): void;

    // SIGNALS
    colorChanged(color: { r: number, g: number, b: number, a: number }): void;
    dataChanged(): void;
    enabledChanged(onOff: boolean): void;
    flippedHorizontalChanged(onOff: boolean): void;
    flippedVerticalChanged(onOff: boolean): void;
    imageChanged(filename: string): void;
    invertedChanged(onOff: boolean): void;
    labelChanged(label: string): void;
    offsetChanged(offset: Point): void;
    opacityChanged(opacity: number): void;
    rotationChanged(rotation: Rotation): void;
    scaleChanged(x: number, y: number): void;
}

/**
 * Layers are used in image editing to manipulate the final values of pixels in an image, in a non-destructive way. Layers exist in a stack. Layers that are higher in the stack impact layers that are lower in the stack. Transparent and/or translucent pixels in one layer allow the pixels in the next lower layer to be revealed. Layers can also be used to blend the values of pixels together in various ways. See Also: DzLayeredTexture
 */
declare class DzTextureLayer {
    blendMode(): BlendMode;

    blendModeAsLabel(mode: BlendMode): string;
    clearMask(): void;
    createMask(maskLabel: string): DzTextureMask;
    getMask(): DzTextureMask;
    needsRefresh(): boolean;
    setMask(mask: DzTextureMask): void;

    // SIGNALS
    aboutToChangeMask(oldMask: DzTextureMask, newMask: DzTextureMask): void;
    blendModeChanged(mode: BlendMode): void;
    maskChanged(oldMask: DzTextureMask, newMask: DzTextureMask): void;
}

/**
 * A texture mask is used in a non-destructive process to hide some portions of a texture layer and reveal others. White values in the mask allow the full value of the underlying texture layer to be shown, and black values in the mask completely block the underlying texture layer from being shown. The range of values between white and black gradually transition between completely shown and completely blocked. When color values are used in the mask, the value of each RGB channel in the color has the same effect on whether or not that channel is shown or blocked. See Also: DzLayeredTexture
 */
declare class DzTextureMask {
}

/**
 * See Also: DzImageProperty DzNumericProperty
 */
declare class DzTextureModifier {
    grayscaleMode(): GrayscaleMode;
    horizontalTiles: number;
    horizontalTilingOffset: number;
    invert: boolean;
    offset: number;
    scale: number;
    verticalTiles: number;
    verticalTilingOffset: number;

    calcOffset(modificationFlags: Modifications): number;
    calcOffset(modificationFlags: Modifications, flipPolarity: boolean): number;
    calcScale(modificationFlags: Modifications): number;
    calcScale(modificationFlags: Modifications, flipPolarity: boolean): number;
    duplicate(): DzTextureModifier;
    getAttributes(settings: DzSettings, modFlags: Modifications): void;
    getGrayscaleMode(modificationFlags: Modifications): number;
    getHorizontalTiles(modificationFlags: Modifications): number;
    getHorizontalTilingOffset(modificationFlags: Modifications): number;
    getOffset(modificationFlags: Modifications): number;
    getScale(modificationFlags: Modifications): number;
    getVerticalTiles(modificationFlags: Modifications): number;
    getVerticalTilingOffset(modificationFlags: Modifications): number;
    isDefault(modificationFlags: Modifications): boolean;
    isInverted(modificationFlag: Modifications, flipPolaritys: boolean): boolean;
    isInverted(modificationFlags: Modifications): boolean;
    reset(): void;
    setAttributes(settings: DzSettings, modFlags: Modifications, oldMod: DzTextureModifier): void;

    // SIGNALS
    grayscaleModeChanged(): void;
    horizontalTilesChanged(): void;
    horizontalTilingOffsetChanged(): void;
    invertedChanged(): void;
    offsetChanged(): void;
    scaleChanged(): void;
    settingsChanged(): void;
    verticalTilesChanged(): void;
    verticalTilingOffsetChanged(): void;
}

/**
 * DzTime is used for storing and passing time values. Time references in DAZ Studio are stored in 'ticks' - there are 4800 ticks per second. This number was chosen because of its divisibility by typical frame rates. For example, at 60 fps (frames per second) there are 80 ticks between each frame; at 30 fps, 160 ticks; at 20 fps, 180 ticks; etc. Attention: Methods throughout the DAZ Studio API that take a DzTime as an argument can also take a Number in its place. Example:
 */
declare class DzTime {
    valueOf(): number;
}

/**
 * Provides a time editor.
 */
declare class DzTimeEdit {
    max(): Date;
    min: Date;
    separator: string;

    // SIGNALS
    valueChanged(arg0: number): void;
}

/**
 * Provides repetitive and single-shot timers.
 */
declare class DzTimer {
    active(): boolean;
    interval: number;
    singleShot: number;

    start(msec: number): void;
    start(): void;
    stop(): void;

    // SIGNALS
    timeout(): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzTimeRange {
    end(): number;
    start: number;

    add(time: number): void;
    extendEndsBy(time: number): void;
    getDuration(): number;
    include(time: number): void;
    include(range: DzTimeRange): void;
    intersect(range: DzTimeRange): void;
    isEmpty(): boolean;
    isIncluded(time: number): boolean;
    isIncluded(range: DzTimeRange): boolean;
    makeEmpty(): void;
    overlaps(range: DzTimeRange): boolean;
    subtract(time: number): void;
    toString(): string;
}

/**
 * This class provides access to a toolbar within the interface. This class is not intended to be constructed directly, rather an instance of the class is created using DzPaneMgr :: createToolBar (). See Also: DzPaneMgr :: removeToolBar () DzPaneMgr :: removeAllToolBars () DzPaneMgr :: hideAllToolBars () DzPaneMgr :: getNumToolBars () DzPaneMgr :: getToolBar () DzPaneMgr :: findToolBar () DzPaneMgr :: getToolBarList ()
 */
declare class DzToolBar {
    floating(): boolean;

    clear(): void;
    dock(area: DockArea, beforeBar: string): void;
    dockedArea(): DockArea;
    getItem(which: number): DzToolBarItem;
    getItemList(): any[];
    getNumItems(): number;
    hasItems(): boolean;
    insertAction(action: DzAction, before: DzAction): void;
    insertAction(action: string, index: number): void;
    insertCustomAction(action: string, index: number): void;
    insertCustomWidget(uiScript: string, index: number): void;
    insertItem(item: DzToolBarItem, index: number): void;
    insertSeparator(index: number): void;
    insertViewportAlignmentSpacer(alignment: number, index: number): void;
    insertViewportCenterAlignSpacer(index: number): void;
    insertViewportLeftAlignSpacer(index: number): void;
    isClosed(): boolean;
    removeItem(index: number): void;
    removeItem(item: DzToolBarItem): void;
    setClosed(onOff: boolean): void;
    undock(pos: Point): void;

    // SIGNALS
    itemListChanged(): void;
}

/**
 * This class provides access to toolbar items within the interface. This class is not intended to be constructed directly, rather an instance of the class is created using one of the following: DzToolBar :: insertAction () DzToolBar :: insertCustomAction () DzToolBar :: insertSeparator () DzToolBar :: insertCustomWidget () DzToolBar :: insertViewportCenterAlignSpacer () DzToolBar :: insertViewportLeftAlignSpacer () DzToolBar :: insertViewportAlignmentSpacer ()
 */
declare class DzToolBarItem {
    action(): string;
    type: Type;
    uiScript: string;
}

/**
 * This container type does not directly support assets. The primary purpose of this container type is to serve as the top-most container in an asset containers hierarchy.
 */
declare class DzTopLevelAssetContainer {
    getState(): ContainerState;
    setState(state: ContainerState): void;

    // SIGNALS
    stateChanged(state: ContainerState): void;
}

/**
 * Attention: This object is provided by the Transfer Utility plugin. It is only available when the Transfer Utility plugin is activated and enabled. Since: 4.6.2.85
 */
declare class DzTransferUtility {
    doTransfer(): boolean;
    getAdaptiveTolerance(): number;
    getAddSmoothModifier(): boolean;
    getAdjustTargetBase(): boolean;
    getConsiderLinesAsRigid(): boolean;
    getContentType(): string;
    getDistanceSquaredTolerance(): number;
    getFitToFigure(): boolean;
    getLockViewOnTransfer(): boolean;
    getMergeHierarchies(): boolean;
    getMorphTransferList(): any[];
    getNearness(): number;
    getOverrideExistingMorphs(): boolean;
    getParentToFigure(): boolean;
    getProjectionTemplatePath(): string;
    getRemoveOriginalTarget(): boolean;
    getRemoveUnusedTargetBones(): boolean;
    getRemoveUnusedTargetBonesIsGreedy(): boolean;
    getRespectHiddenFacets(): boolean;
    getSmartLeftRightHandling(): boolean;
    getSourceBase(): BaseType;
    getSourceBaseMorph(): DzMorph;
    getSourceGeom(): DzShape;
    getSourceNode(): DzNode;
    getSourceType(): AssetType;
    getTargetBase(): BaseType;
    getTargetBaseMorph(): DzMorph;
    getTargetGeom(): DzShape;
    getTargetNode(): DzNode;
    getTargetOutputFigure(): DzFigure;
    getTargetReplacesSource(): boolean;
    getTargetType(): AssetType;
    getTransferBinding(): boolean;
    getTransferFaceGroups(): boolean;
    getTransferMaterialGroups(): boolean;
    getTransferMorphs(): boolean;
    getTransferRegionGroups(): boolean;
    getTransferSelectionMap(): boolean;
    getTransferSourceMorphs(): SourceMorphTransferType;
    getTransferTemplateMorphs(): boolean;
    getTransferUVs(): boolean;
    getUseNearness(): boolean;
    getUseSpecifiedContentType(): boolean;
    getUVSpaceProjection(): boolean;
    getVertexFirstProjection(): boolean;
    isSourceBaseMorphClone(): boolean;
    removeUnusedBones(figure: DzFigure): void;
    setAdaptiveTolerance(val: number): void;
    setAddSmoothModifier(yesNo: boolean): void;
    setAdjustTargetBase(onOff: boolean): void;
    setConsiderLinesAsRigid(onOff: boolean): void;
    setContentType(conType: string): void;
    setDistanceSquaredTolerance(val: number): void;
    setFitToFigure(yesNo: boolean): void;
    setLockViewOnTransfer(onOff: boolean): void;
    setMergeHierarchies(onOff: boolean): void;
    setMorphTransferList(list: any[]): void;
    setNearness(val: number): void;
    setOverrideExistingMorphs(onOff: boolean): void;
    setParentToFigure(yesNo: boolean): void;
    setProjectionTemplatePath(path: string): void;
    setRemoveOriginalTarget(onOff: boolean): void;
    setRemoveUnusedTargetBones(onOff: boolean): void;
    setRemoveUnusedTargetBonesIsGreedy(onOff: boolean): void;
    setRespectHiddenFacets(onOff: boolean): void;
    setSilentImporters(onOff: boolean): void;
    setSmartLeftRightHandling(onOff: boolean): void;
    setSource(node: DzNode): boolean;
    setSource(geom: DzShape): boolean;
    setSourceBaseCurrent(): boolean;
    setSourceBaseMorph(morph: DzMorph): boolean;
    setTarget(node: DzNode): boolean;
    setTarget(geom: DzShape): boolean;
    setTargetBaseCurrent(): boolean;
    setTargetBaseMorph(morph: DzMorph): boolean;
    setTargetReplacesSource(onOff: boolean): void;
    setTransferBinding(onOff: boolean): void;
    setTransferFaceGroups(onOff: boolean): void;
    setTransferMaterialGroups(onOff: boolean): void;
    setTransferMorphs(onOff: boolean): void;
    setTransferRegionGroups(onOff: boolean): void;
    setTransferSelectionMap(onOff: boolean): void;
    setTransferSourceMorphs(type: SourceMorphTransferType): void;
    setTransferTemplateMorphs(onOff: boolean): void;
    setTransferUVs(onOff: boolean): void;
    setUseNearness(onOff: boolean): void;
    setUseSpecifiedContentType(yesNo: boolean): void;
    setUVSpaceProjection(onOff: boolean): void;
    setVertexFirstProjection(onOff: boolean): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzTransformTool {
}

/**
 * A generic asset container that takes on the type of the data assigned to it, which can be used to present hierarchical structures that are representable by a slash ('/') delimted path.
 */
declare class DzTypeAssetContainer {
    data(): any;

    addChildContainer(typePath: string): number;
    addChildContainer(container: DzTypeAssetContainer): number;
    clear(): void;
    findChildContainer(typePath: string): DzTypeAssetContainer;
    getTextPath(ignoreRoot: boolean): string;
    getTypeName(): string;
    insertToSpecificType(asset: DzAsset, typePath: string): boolean;

    // SIGNALS
    aboutToClear(): void;
}

/**
 * This error is thrown by the interpreter to indicate that the actual type of an operand is different than the expected type. See the ECMA script specification for more information.
 */
declare class TypeError {
}

/**
 * See Also: DzExportMgr :: findExporterByClassName () DzExportMgr :: findExporter ()
 */
declare class DzU3DExporter {
}

/**
 * Provides functionality that allows QtDesigner to be used in the creation of graphical user interfaces used by scripts. See Also: designer-manual
 */
declare class DzUiLoader {
    addPluginPath(path: string): void;
    availableLayouts(): any[];
    availableWidgets(): any[];
    clearPluginPaths(): void;
    createLayout(className: string, parent: QObject, name: string): DzLayout;
    createWidget(className: string, parent: DzWidget, name: string): DzWidget;
    load(filePath: string, parent: DzWidget): DzWidget;
    pluginPaths(): any[];
    setWorkingDirectory(dir: string): void;
    workingDirectory(): string;
}

/**
 * TODO: Add detailed description.
 */
declare class DzUIPopUpWgt {
    getFileName(): string;
    getUIWidget(): QWidget;
    getWorkingDirectory(): string;
    loadUI(filename: string): void;
    movePopUp(newPos: Point): void;
    setWidget(widget: QWidget): void;
    setWorkingDirectory(str: string): void;
}

/**
 * Encapsulates a widget loaded from a QtDesigner (*.ui) file. Do not create an instance of this class, request an instance via DzUiLoader . See Also: DzUiLoader :: createWidget () DzUiLoader :: load ()
 */
declare class DzUiWidget {
}

/**
 * There is only one undo stack in the application, which is created and owned by DzApp . This object is directly available using the Global :: UndoStack variable.
 */
declare class DzUndoStack {
    accept(caption: string): void;
    beginHold(): void;
    cancel(): void;
    canPushItems(): boolean;
    canRedo(): boolean;
    canUndo(): boolean;
    clearAll(): void;
    drop(): void;
    getCaption(offset: number): string;
    getCurrentIndex(): number;
    getNumItems(): number;
    getNumRedoItems(): number;
    getNumUndoItems(): number;
    getRedoCaption(): string;
    getUndoCaption(): string;
    hasItems(): boolean;
    isInUndoRedo(): boolean;
    lock(): void;
    redo(): boolean;
    undo(): boolean;
    unlock(): void;

    // SIGNALS
    redoAvailable(yesNo: boolean): void;
    redoCaptionChanged(caption: string): void;
    undoAvailable(yesNo: boolean): void;
    undoCaptionChanged(caption: string): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzUniversalRotateTool {
}

/**
 * TODO: Add detailed description.
 */
declare class DzUniversalScaleTool {
}

/**
 * Since: 4.11.0.53
 */
declare class DzUniversalTool {
    getAdjustedCoordinateSpace(node: DzNode): CoordinateSpace;
    getCoordinateSpace(): CoordinateSpace;
    getGuidesColor(): { r: number, g: number, b: number, a: number };
    getRotateSecondaryNodes(): boolean;
    getScaleSecondaryNodes(): boolean;
    getShowGuides(): boolean;
    getShowHomeMenu(): boolean;
    getShowPinsMenu(): boolean;
    getShowRotateFreeHandle(): boolean;
    getShowRotateGizmo(): boolean;
    getShowRotateScreenHandle(): boolean;
    getShowRotateXHandle(): boolean;
    getShowRotateYHandle(): boolean;
    getShowRotateZHandle(): boolean;
    getShowScaleGizmo(): boolean;
    getShowScaleUniformHandle(): boolean;
    getShowScaleXHandle(): boolean;
    getShowScaleYHandle(): boolean;
    getShowScaleZHandle(): boolean;
    getShowTranslateGizmo(): boolean;
    getShowTranslateScreenHandle(): boolean;
    getShowTranslateXHandle(): boolean;
    getShowTranslateYHandle(): boolean;
    getShowTranslateZHandle(): boolean;
    getSnapRotation(): boolean;
    getSnapRotationValue(): number;
    getSnapScale(): boolean;
    getSnapScaleValue(): number;
    getSnapTranslation(): boolean;
    getSnapTranslationValue(): number;
    getTransformSecondaryNodes(): boolean;
    getTranslateSecondaryNodes(): boolean;
    providesGuide(): boolean;
    providesRotation(): boolean;
    providesScale(): boolean;
    providesTranslation(): boolean;
    setCoordinateSpace(space: CoordinateSpace): void;
    setGuidesColor(color: { r: number, g: number, b: number, a: number }): void;
    setRotateSecondaryNodes(yesNo: boolean): void;
    setScaleSecondaryNodes(yesNo: boolean): void;
    setShowGuides(yesNo: boolean): void;
    setShowHomeMenu(yesNo: boolean): void;
    setShowPinsMenu(yesNo: boolean): void;
    setShowRotateFreeHandle(yesNo: boolean): void;
    setShowRotateGizmo(yesNo: boolean): void;
    setShowRotateScreenHandle(yesNo: boolean): void;
    setShowRotateXHandle(yesNo: boolean): void;
    setShowRotateYHandle(yesNo: boolean): void;
    setShowRotateZHandle(yesNo: boolean): void;
    setShowScaleGizmo(yesNo: boolean): void;
    setShowScaleUniformHandle(yesNo: boolean): void;
    setShowScaleXHandle(yesNo: boolean): void;
    setShowScaleYHandle(yesNo: boolean): void;
    setShowScaleZHandle(yesNo: boolean): void;
    setShowTranslateGizmo(yesNo: boolean): void;
    setShowTranslateScreenHandle(yesNo: boolean): void;
    setShowTranslateXHandle(yesNo: boolean): void;
    setShowTranslateYHandle(yesNo: boolean): void;
    setShowTranslateZHandle(yesNo: boolean): void;
    setSnapRotation(yesNo: boolean): void;
    setSnapRotationValue(value: number): void;
    setSnapScale(yesNo: boolean): void;
    setSnapScaleValue(value: number): void;
    setSnapTranslation(yesNo: boolean): void;
    setSnapTranslationValue(value: number): void;
    setTransformSecondaryNodes(yesNo: boolean): void;
    setTranslateSecondaryNodes(yesNo: boolean): void;

    // SIGNALS
    coordinateSpaceChanged(space: CoordinateSpace): void;
    guidesColorChanged(color: { r: number, g: number, b: number, a: number }): void;
    rotateSecondaryNodesChanged(yesNo: boolean): void;
    scaleSecondaryNodesChanged(yesNo: boolean): void;
    showGuidesChanged(yesNo: boolean): void;
    showHomeMenuChanged(yesNo: boolean): void;
    showPinsMenuChanged(yesNo: boolean): void;
    showRotateFreeHandleChanged(yesNo: boolean): void;
    showRotateGizmoChanged(yesNo: boolean): void;
    showRotateScreenHandleChanged(yesNo: boolean): void;
    showRotateXHandleChanged(yesNo: boolean): void;
    showRotateYHandleChanged(yesNo: boolean): void;
    showRotateZHandleChanged(yesNo: boolean): void;
    showScaleGizmoChanged(yesNo: boolean): void;
    showScaleUniformHandleChanged(yesNo: boolean): void;
    showScaleXHandleChanged(yesNo: boolean): void;
    showScaleYHandleChanged(yesNo: boolean): void;
    showScaleZHandleChanged(yesNo: boolean): void;
    showTranslateGizmoChanged(yesNo: boolean): void;
    showTranslateScreenHandleChanged(yesNo: boolean): void;
    showTranslateXHandleChanged(yesNo: boolean): void;
    showTranslateYHandleChanged(yesNo: boolean): void;
    showTranslateZHandleChanged(yesNo: boolean): void;
    snapRotationChanged(yesNo: boolean): void;
    snapRotationValueChanged(value: number): void;
    snapScaleChanged(yesNo: boolean): void;
    snapScaleValueChanged(value: number): void;
    snapTranslationChanged(yesNo: boolean): void;
    snapTranslationValueChanged(value: number): void;
    transformSecondaryNodesChanged(yesNo: boolean): void;
    translateSecondaryNodesChanged(yesNo: boolean): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzUniversalTranslateTool {
}

/**
 * Represents a URI as it is used for the DSON file format. DzUri provides functionality in addition to standard URI / URL representations that is specific to the DSON file format. DzUri provides for a traditional URI with path and fragment portions. In addition, it further divides the fragment into 1 to 3 parts for ease of use in the DSON file format. The following is an example of a URI as represented by the DzURI class: /Converted/Victoria4/Victoria4.dsf::rCollar?rotation/x The file path portion of this URI is: “/Converted/Victoria4/Victoria4.dsf” The fragment portion of this URI is: “rCollar?rotation/x” The fragment is further divided into an identifier and a property path. In this case the identifier is “rCollar” and the property path is “rotation/x”. All the sections of the fragment are optional, however, to be valid, each section in the fragment requires the preceding section to also be valid. So, the following URIs are valid: /Converted/Victoria4/Victoria4.dsf::rCollar /Converted/Victoria4/Victoria4.dsf::rCollar?rotation /Converted/Victoria4/Victoria4.dsf::rCollar?rotation/x And the following URIs are not valid: /Converted/Victoria4/Victoria4.dsf#?rotation/x /Converted/Victoria4/Victoria4.dsf#?/x /Converted/Victoria4/Victoria4.dsf#?rotation Since: 4.8.1.18
 */
declare class DzUri {
    filePath(): string;
    fileVersion: DzVersion;
    id: string;
    isCloudFileUri: boolean;
    modifierPath: any[];
    nodePath: any[];
    propertyPath: any[];
    schemeType: SchemeType;

    escape(str: string, exclude: ByteArray, closer: ByteArray): string;
    escapedPath(list: any[], exclude: ByteArray, include: ByteArray): string;
    fromLocalFilename(filePath: string): DzUri;
    unescape(str: string): string;
    unescapePath(path: string): any[];
    clear(): void;
    clearFoundLocalFilename(): void;
    detach(): void;
    isEmpty(): boolean;
    isNull(): boolean;
    setUri(uri: string): void;
    toLocalFilename(preferredPath: string): string;
    toLocalFilename(): string;
    toPath(preferredPath: string): string;
    toString(): string;
    toString(flags: PartFlags): string;
}

/**
 * This error is thrown by the interpreter to indicate that one of the global URI handling functions was used in a way that is incompatible with its definition. See the ECMA script specification for more information.
 */
declare class URIError {
}

/**
 * Any DrawStyle which should be available to the user for selecting need to be derived from this class.
 */
declare class DzUserDrawStyle {
    isEnabled(): boolean;

    getDescription(): string;
    getPixmap(): Pixmap;
}

/**
 * TODO: Add detailed description.
 */
declare class DzUVSet {
    assetAuthor(): DzAuthor;
    assetFileRevision: DzVersion;
    assetId: string;
    assetModifiedDate: Date;
    assetNeedSave: boolean;
    assetSource: DzUri;
    assetUri: DzUri;

    // SIGNALS
    assetModified(): void;
    assetWasSaved(): void;
}

/**
 * An asset save filter for saving a UV Set Definition Support Asset in the DSON format. See Also: Sample: Save a UV Set Definition Support Asset
 */
declare class DzUVSupportAssetFilter {
}

/**
 * Provided as a convenience for creating a DzBoxLayout where the direction is automatically initially set to DzBoxLayout :: TopToBottom .
 */
declare class DzVBoxLayout {
}

/**
 * Provides a DzButtonGroup with a vertical layout. Deprecated Exists only to keep old code working. Do not use in new code. Use DzButtonGroup for state management and DzGroupBox in conjunction with DzVBoxLayout for visual representation instead.
 */
declare class DzVButtonGroup {
}

/**
 * See Also: DzVec3 DzInt2 Since: 4.6.4.88
 */
declare class DzVec2 {
    x(): number;
    y: number;

    abs(): void;
    add(vec: DzVec2): DzVec2;
    average(): number;
    clamp(min: number, max: number): void;
    clamped(min: number, max: number): DzVec2;
    clampedMax(max: number): DzVec2;
    clampedMin(min: number): DzVec2;
    clampMax(max: number): void;
    clampMin(min: number): void;
    cross(vec: DzVec2): DzVec2;
    divide(vec: DzVec2): DzVec2;
    dot(vec: DzVec2): number;
    equals(vec: DzVec2, tolerance: number): boolean;
    getAngleTo(vec: DzVec2): number;
    identity(): DzVec2;
    length(): number;
    lengthSquared(): number;
    linearInterp(t: number, v1: DzVec2, v2: DzVec2): DzVec2;
    makeIdentity(): void;
    makeZero(): void;
    modulate(min: number, max: number): DzVec2;
    modulo(min: number, max: number): void;
    multiply(vec: DzVec2): DzVec2;
    negate(): void;
    normalize(): void;
    normalized(): DzVec2;
    setLength(length: number): void;
    square(): void;
    subtract(vec: DzVec2): DzVec2;
    toString(): string;
    zero(): DzVec2;
}

/**
 * See Also: DzVec2 DzInt2
 */
declare class DzVec3 {
    x(): number;
    y: number;
    z: number;

    abs(): void;
    add(vec: DzVec3): DzVec3;
    average(): number;
    clamp(min: number, max: number): void;
    clamped(min: number, max: number): DzVec3;
    clampedMax(max: number): DzVec3;
    clampedMin(min: number): DzVec3;
    clampMax(max: number): void;
    clampMin(min: number): void;
    cross(vec: DzVec3): DzVec3;
    divide(vec: DzVec3): DzVec3;
    dot(vec: DzVec3): number;
    equals(vec: DzVec3, tolerance: number): boolean;
    getAngleTo(vec: DzVec3): number;
    getRotationTo(vec: DzVec3): DzQuat;
    identity(): DzVec3;
    length(): number;
    lengthSquared(): number;
    linearInterp(t: number, v1: DzVec3, v2: DzVec3): DzVec3;
    makeIdentity(): void;
    makeZero(): void;
    modulate(min: number, max: number): DzVec3;
    modulo(min: number, max: number): void;
    multiply(vec: DzVec3): DzVec3;
    negate(): void;
    normalize(): void;
    normalized(): DzVec3;
    setLength(length: number): void;
    square(): void;
    subtract(vec: DzVec3): DzVec3;
    toString(): string;
    zero(): DzVec3;
}

/**
 * This class was added to DAZ Studio 4.x to make it easier to work with 64-bit version numbers and to facilitate compatibility with the old 32-bit version numbers. Version numbers are typically displayed to the user as short version strings, e.g. 4.0, or long version strings, e.g. 4.0.0.0. The version number consists of 4 components: The Major version number, the Minor version number, the Revision number, and the Build number. This is displayed in the following order: Major.Minor.Revision.Build. In DAZ Studio, version numbers are typically stored as 64-bit unsigned integers with 16 bits for each number. This means that each number has a valid range of 0-65535. The most significant 16 bits are the Major version number, the next most significant 16 bits are the Minor version number, the next most significant 16 bits are the Revision number and the least significant 16 bits are the Build number. So, a packed version number in hexadecimal notation might look like: 0x1111222233334444 where 1111 is the Major version number, 2222 is the Minor version number 3333 is the Revision number and 4444 is the build number. It is recommended that this class be used when possible to reduce confusion when dealing with version numbers in code. This class provides methods for all of the numerical comparison operators ( <, >, ⇐, >=, ==, != ) to make it easy to compare version numbers without directly using the packed value, or the individual components. Since: 4.8.1.20
 */
declare class DzVersion {
    fromString(versionStr: string): DzVersion;
    equal(version: DzVersion): boolean;
    getBuildNumber(): number;
    getLongVersionString(): string;
    getMajorVersion(): number;
    getMinorVersion(): number;
    getRevisionNumber(): number;
    getVersionNumber(): number;
    getVersionNumber32(): number;
    getVersionString(): string;
    greaterThan(version: DzVersion): boolean;
    greaterThanOrEqual(version: DzVersion): boolean;
    isValid(): boolean;
    lessThan(version: DzVersion): boolean;
    lessThanOrEqual(version: DzVersion): boolean;
    notEqual(version: DzVersion): boolean;
    setVersionNumber(version: number): void;
    setVersionNumber(major: number, minor: number, revision: number, build: number): void;
    toString(): string;
}

/**
 * Represents a list of vertices from a geometry that are collected into a group. The group is stored as a list of integers which are indices into the vertex list of the geometry which this group references. See Also: DzVertexMesh
 */
declare class DzVertexGroup {
    getOwner(): DzGeometry;
}

/**
 * This class maps an arbitrary numeric value to a vertex in the geometry. It should always contain at a minimum one value per vertex. It also supports discontinuous vertex maps - where different facets can have different values for the same vertex.
 */
declare class DzVertexMap {
    addDctFloatValue(vertexIdx: number, facetIdx: number, val: number): void;
    addDctIntValue(vertexIdx: number, facetIdx: number, val: number): void;
    addDctPnt2Vec(vertexIdx: number, facetIdx: number, val: DzVec3): void;
    addDctPnt3Vec(vertexIdx: number, facetIdx: number, val: DzVec3): void;
    addDctShortValue(vertexIdx: number, facetIdx: number, val: number): void;
    clearDiscontinuousData(): void;
    getMapIndex(vertexIdx: number, facetIdx: number): number;
    getNumDiscontinuousVerts(): number;
    getTargetVertexCount(): number;
    preSizeDiscontinuous(disconCount: number): void;
    setDctIndex(vertexIdx: number, facetIdx: number, mapIdx: number): void;
    setTargetVertexCount(vertCount: number): void;
    squeezeDiscontinuous(): void;
    updateDctValue(oldIdx: number, newIdx: number, facetIdx: number): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzVertexMesh {
    activateVertexGroup(name: string): void;
    addToVertexGroup(name: string): void;
    addVertex(x: number, y: number, z: number): number;
    addVertex(pnt: DzVec3): number;
    addVerticesFromMesh(mesh: DzVertexMesh): void;
    beginVertexSelectionEdit(): void;
    createVertexGroup(name: string): boolean;
    deactivateAllVertexGroups(): void;
    deactivateVertexGroup(name: string): void;
    finishVertexSelectionEdit(): void;
    getActiveVertexGroup(index: number): DzVertexGroup;
    getLockedVertices(): any[];
    getNumActiveVertexGroups(): number;
    getNumVertexGroups(): number;
    getNumVertices(): number;
    getSelectedVertices(): any[];
    getUnusedVertices(): any[];
    getVertex(index: number): DzVec3;
    getVertexGroup(index: number): DzVertexGroup;
    invertVertexSelection(): void;
    isVertexLocked(index: number): boolean;
    isVertexSelected(index: number): boolean;
    preSizeVertexArray(numVerts: number): DzError;
    selectAllVertices(onOff: boolean): void;
    selectVertex(index: number, onOff: boolean): void;
    selectVerticesByIndexList(list: DzIndexList, onOff: boolean): void;
    setVertex(index: number, pnt: DzVec3): void;
    setVertexArray(numVerts: number): void;

    // SIGNALS
    topologyChanged(): void;
    vertexSelectionChanged(): void;
}

/**
 * Provides a DzGroupBox with a vertical layout.
 */
declare class DzVGroupBox {
}

/**
 * TODO: Add detailed description.
 */
declare class DzVideoClip {
    appendFrame(img: Image): void;
    appendFrameFile(imgFilename: string): void;
    getAudio(): DzAudioClip;
    getAudioStartTime(): number;
    getFrame(i: number): Image;
    getFrameRate(): number;
    getHeight(): number;
    getNumFrames(): number;
    getWidth(): number;
    setAudio(audio: DzAudioClip, audioStartTime: number): void;
    setFrameRate(rate: number): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzVideoExporter {
    getDescription(): string;
    getExtension(): string;
    isFileExporter(): boolean;
    saveClip(filename: string, clip: DzVideoClip): DzError;
    saveClip(filename: string, clip: DzVideoClip, options: DzFileIOSettings): DzError;
}

/**
 * A DzView is a widget that consists of a toolbar (for providing access to associated camera controls) and a veiw selection menu button (for selecting which camera to view through), that can be displayed to the user within a DzViewport .
 */
declare class DzView {
    getDescription(): string;
    getIcon(): Pixmap;
}

/**
 * A DzViewport is a widget that consists of a Dz3DViewport , an optional alternate DzView , and an indicator of the viewport's active state (for cases where multiple instances are displayed to the user at the same time).
 */
declare class DzViewport {
    get3DViewport(): Dz3DViewport;
    getManager(): DzViewportMgr;
    getView(): DzView;
    isCustom(): boolean;
    setView(view: DzView): void;
    setViewVisible(onOff: boolean): void;

    // SIGNALS
    dimensionsChanged(): void;
    view3dCurrentDimensionsChanged(): void;
    viewChanged(view: DzView): void;
}

/**
 * Responsible for the management of viewports, general options related to how viewports (or the items within them) are drawn or operated on, and the tools that operate within the context of a viewport. There is only one instance of this manager in an application. This instance is created and owned by DzMainWindow . Request the instance via DzMainWindow :: getViewportMgr (). See Also: Global :: MainWindow DzViewport Dz3DViewport DzUserDrawStyle DzViewTool Samples: View Tools
 */
declare class DzViewportMgr {
    getNumUserDrawStyles(): number;
    getNumViews(): number;
    getUserDrawStyle(i: number): DzUserDrawStyle;
    getView(i: number): DzView;
    getViewDescription(i: number): string;
    activateNextTool(): void;
    activatePrevTool(): void;
    applyStyleColors(): void;
    clearOverrideTool(): void;
    findTool(className: string): DzViewTool;
    findUserDrawStyle(description: string): DzUserDrawStyle;
    getActiveTool(): DzViewTool;
    getActiveViewport(): DzViewport;
    getCustomViewport(i: number): DzViewport;
    getDefaultViewport(i: number): DzViewport;
    getDrawSettingsElementList(): any[];
    getInvertMouseWheel(): boolean;
    getLayout(): Layout;
    getMouseBtnAccelerator(operation: ViewOperation): ViewMouseBtnAccelerator;
    getMouseBtnAccelerator(button: MouseButton, modifiers: KeyboardModifiers): ViewMouseBtnAccelerator;
    getMouseBtnAccelerator(mouseBtn: number, ctrl: boolean, alt: boolean, shift: boolean): ViewMouseBtnAccelerator;
    getMouseBtnAccelerator(str: string): ViewMouseBtnAccelerator;
    getMouseBtnAcceleratorString(accel: ViewMouseBtnAccelerator): string;
    getMouseBtnAcceleratorString(operation: ViewOperation): string;
    getMouseDragScalar(): number;
    getMouseModifier(str: string): ViewMouseModifier;
    getMouseModifier(modifiers: KeyboardModifiers): ViewMouseModifier;
    getMouseModifier(ctrl: boolean, alt: boolean, shift: boolean): ViewMouseModifier;
    getMouseModifierString(accel: ViewMouseModifier): string;
    getMouseWheelScalar(): number;
    getNodeClickMode(): number;
    getNumCustomViewports(): number;
    getNumDefaultViewports(): number;
    getNumTools(): number;
    getNumViewCameras(): number;
    getNumViewports(): number;
    getNumVisibleCustomViewports(): number;
    getNumVisibleDefaultViewports(): number;
    getNumVisibleViewports(): number;
    getOperation(accel: ViewMouseBtnAccelerator): ViewOperation;
    getOverrideTool(): DzViewTool;
    getPropagateBackgroundColor(): boolean;
    getQuickDrawMode(): QDMode;
    getRegionClickMode(): number;
    getTool(i: number): DzViewTool;
    getUsePerPixelLighting(): boolean;
    getViewCamera(type: CameraType): DzCamera;
    getViewCamera(i: number): DzCamera;
    getViewport(i: number): DzViewport;
    isManipulationBindingOn(): boolean;
    isSubDManipulationOn(): boolean;
    repaintActive3DViewport(): void;
    resetViewCameras(): void;
    setActiveTool(i: number): void;
    setActiveTool(tool: DzViewTool): void;
    setActiveViewport(activeView: DzViewport): void;
    setInvertMouseWheel(onOff: boolean): void;
    setLayout(val: Layout): void;
    setManipulationBindingOn(onOff: boolean): void;
    setMouseBtnAccelerator(operation: ViewOperation, accel: ViewMouseBtnAccelerator): void;
    setMouseDragScalar(val: number): void;
    setMouseWheelScalar(val: number): void;
    setNodeClickMode(mode: number): void;
    setOverrideTool(viewTool: DzViewTool): void;
    setPropagateBackgroundColor(onOff: boolean): void;
    setQuickDrawMode(mode: QDMode): void;
    setRegionClickMode(mode: number): void;
    setSubDManipulationOn(onOff: boolean): void;
    setUsePerPixelLighting(onOff: boolean): void;
    setViewRatios(hSingle: number, h1: number, h2: number, vSingle: number, v1: number, v2: number): void;
    validateMouseBtnAccelerator(accel: ViewMouseBtnAccelerator): boolean;
    validateMouseWheelAccelerator(accel: ViewMouseModifier): boolean;

    // SIGNALS
    accelChanged(operation: ViewOperation, accel: ViewMouseBtnAccelerator): void;
    acceleratorsChanged(): void;
    acitve3DViewCurrentDimensionsChanged(): void;
    activeToolDrawnDataChanged(): void;
    activeToolSwitched(): void;
    activeViewResized(): void;
    activeViewSwitched(): void;
    contextMenuAboutToShow(menu: DzMenu, view: Dz3DViewport, pos: Point): void;
    drawElementsListChanged(): void;
    graftDrawingChanged(): void;
    invertMouseWheelChanged(onOff: boolean): void;
    manipFinished(): void;
    manipStarted(): void;
    manipulationBindingChanged(onOff: boolean): void;
    mouseDragScalarChanged(scalar: number): void;
    mouseWheelScalarChanged(scalar: number): void;
    nodeClickModeChanged(mode: number): void;
    propagateBackgroundColorChanged(onOff: boolean): void;
    quickDrawModeChanged(mode: QDMode): void;
    redrawsLocked(onOff: boolean): void;
    regionClickModeChanged(mode: number): void;
    subDManipulationChanged(onOff: boolean): void;
    toolListChanged(): void;
    viewLayoutChanged(): void;
    viewportCameraListChanged(): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzViewRenderHandler {
}

/**
 * A DzViewTool is a tool that functions in concert with a 3D viewport. View tools are registered with the DzViewportMgr singleton and can be accessed/modified via script.
 */
declare class DzViewTool {
    getOptionsMenu(): DzActionMenu;

    // SIGNALS
    activated(): void;
    deactivated(): void;
    drawnDataChanged(): void;
    rebuildMenu(): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzViewToolAction {
    getToolClassName(): string;
}

/**
 * An asset save filter for saving a Wearable(s) Preset in the DSON format. See Also: Sample: Save a Wearable(s) Preset
 */
declare class DzWearablesAssetFilter {
}

/**
 * TODO: Add detailed description.
 */
declare class DzWeightMap {
    clearAffectedWeights(): void;
    detach(): void;
    empty(): void;
    getFloatWeight(idx: number): number;
    getNumAffected(): number;
    getNumWeights(): number;
    getStrengthControl(): DzFloatProperty;
    hasNonZeroWeight(): boolean;
    isEmpty(): boolean;
    isLocked(): boolean;
    isPersistent(): boolean;
    merge(map: DzWeightMap): void;
    setFloatWeight(idx: number, weight: number): void;
    setLocked(onOff: boolean): void;
    setNumWeights(nWeights: number, keepExisting: boolean): void;
    setPersistent(onOff: boolean): void;
    getStrengthController(): DzFloatProperty;

    // SIGNALS
    weightValuesChanged(): void;
}

/**
 * TODO: Add detailed description.
 */
declare class DzWeld {
    getTargetBone(): DzBone;
    getWeldBone(): DzBone;
    setTargetBone(targetBone: DzBone): void;
    setWeldBone(weldBone: DzBone): void;

    // SIGNALS
    targetBoneChanged(): void;
    weldBoneChanged(): void;
}

/**
 * Base class for all wrapped widgets. This is an abstract base class that provides general functionality for script widget components.
 */
declare class DzWidget {
    colorCount(): number;
    depth: number;
    enabled: boolean;
    font: Font;
    globalX: number;
    globalY: number;
    height: number;
    heightMM: number;
    logicalDpiX: number;
    logicalDpiY: number;
    maxHeight: number;
    maxWidth: number;
    minHeight: number;
    minWidth: number;
    palette: Palette;
    paletteBackgroundColor: { r: number, g: number, b: number, a: number };
    paletteBackgroundPixmap: Pixmap;
    paletteForegroundColor: { r: number, g: number, b: number, a: number };
    physicalDpiX: number;
    physicalDpiY: number;
    toolTip: string;
    whatsThis: string;
    width: number;
    widthMM: number;
    x: number;
    y: number;

    findChildOfWidget(name: string): DzWidget;
    getChildrenOfWidget(name: string): any[];
    getLayout(): DzLayout;
    getWidget(): QWidget;
    grab(rectangle: Rect): Pixmap;
    grab(x: number, y: number, width: number, height: number): Pixmap;
    hide(): void;
    mapFrom(parent: DzWidget, pos: Point): Point;
    mapFromGlobal(pos: Point): Point;
    mapFromParent(pos: Point): Point;
    mapTo(parent: DzWidget, pos: Point): Point;
    mapToGlobal(pos: Point): Point;
    mapToParent(pos: Point): Point;
    reparent(parent: DzWidget, pnt: Point, showIt: boolean): void;
    setFixedHeight(height: number): void;
    setFixedSize(width: number, height: number): void;
    setFixedWidth(width: number): void;
    setGeometry(x: number, y: number, w: number, h: number): void;
    show(): void;
}

/**
 * This pages exists in order to indicate the script accessible properties and signals of the Qt native QWidget class.
 */
declare class QWidget {
    acceptDrops(): boolean;
    accessibleDescription: string;
    accessibleName: string;
    autoFillBackground: boolean;
    baseSize: Size;
    childrenRect: Rect;
    enabled: boolean;
    focus: boolean;
    font: Font;
    frameGeometry: Rect;
    frameSize: Size;
    fullScreen: boolean;
    geometry: Rect;
    height: number;
    isActiveWindow: boolean;
    maximized: boolean;
    maximumHeight: number;
    maximumSize: Size;
    maximumWidth: number;
    minimized: boolean;
    minimumHeight: number;
    minimumSize: Size;
    minimumSizeHint: Size;
    minimumWidth: number;
    mouseTracking: boolean;
    normalGeometry: Rect;
    palette: Palette;
    pos: Point;
    rect: Rect;
    size: Size;
    sizeHint: Size;
    sizeIncrement: Size;
    statusTip: string;
    styleSheet: string;
    toolTip: string;
    updatesEnabled: boolean;
    visible: boolean;
    whatsThis: string;
    width: number;
    windowFilePath: string;
    windowIconText: string;
    windowModified: boolean;
    windowOpacity: number;
    windowTitle: string;
    x: number;
    y: number;

    close(): boolean;
    hide(): void;
    lower(): void;
    raise(): void;
    repaint(): void;
    setDisabled(disable: boolean): void;
    setEnabled(enabled: boolean): void;
    setFocus(): void;
    setHidden(hidden: boolean): void;
    setStyleSheet(styleSheet: string): void;
    setVisible(visible: boolean): void;
    setWindowModified(modified: boolean): void;
    setWindowTitle(title: string): void;
    show(): void;
    showFullScreen(): void;
    showMaximized(): void;
    showMinimized(): void;
    showNormal(): void;
    update(): void;
}

/**
 * Provides functionality for reading and writing zlib compressed *.zip files.
 */
declare class DzZipFile {
    addDirToZip(pathOnDisk: string, pathInZip: string): boolean;
    addFileToZip(pathOnDisk: string, pathInZip: string): boolean;
    close(): void;
    compressAll(path: string, recursive: boolean): boolean;
    extractAll(basePath: string): boolean;
    extractCurrentFile(basePath: string): boolean;
    getCurrentFileAttributes(): number;
    getCurrentFileComment(): string;
    getCurrentFileCompressedSize(): number;
    getCurrentFileCompressionMethod(): string;
    getCurrentFileCompressionRatio(): number;
    getCurrentFileCRC(): string;
    getCurrentFileDateTime(): Date;
    getCurrentFileIsFolder(): boolean;
    getCurrentFileName(): string;
    getCurrentFileUncompressedSize(): number;
    getFileNames(): any[];
    getGlobalComment(): string;
    getNumEntries(): number;
    goToFirstFile(): boolean;
    goToNextFile(): boolean;
    locateFile(pathInZip: string): boolean;
    open(mode: AccessMode): boolean;
    setGlobalComment(comment: string): boolean;
    getCurrentFileAtributes(): number;
}

//
// 3. GLOBAL VARIABLES (Crucial!)
// THESE MUST REMAIN AT THE TOP OR BOTTOM OF THIS FILE!
//
declare const Scene: DzScene;
declare const App: DzApp;
declare const MainWindow: DzMainWindow;
declare const FileDialog: DzFileDialog;
declare const ColorDialog: DzColorDialog;
declare const UndoStack: DzUndoStack;
declare const Geometry: DzGeometryUtil;
declare const System: DzSystem;
