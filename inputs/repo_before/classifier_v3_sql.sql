CREATE OR REPLACE TABLE workspace.default.volve_ddr_classified AS
SELECT
  filename, wellbore, date_report, md_m, sum24hr,
  CASE
    WHEN n RLIKE '(?i)(36.{0,5}(?:hole|HO|BHA)|30.{0,5}conductor|\\bspud\\b|tagged sea bt|wash.{0,10}down.{0,20}conductor)' THEN 'Spud / Conductor'
    WHEN n RLIKE '(?i)(26.{0,5}(?:hole|BHA|section)|20.{0,5}casing|RIH.{0,20}20.{0,5}cas|running.{0,15}20.{0,5}cas|ran.{0,10}20.{0,5}casing|land.{0,10}20.{0,5}casing)' THEN 'Surface casing'
    WHEN n RLIKE '(?i)(17.{0,3}1.2.{0,5}(?:hole|section|BHA)|17\\.5.{0,5}(?:hole|section)|drilling.{0,15}17.{0,3}(?:1.2|5)|drilled.{0,15}17.{0,3}(?:1.2|5))' THEN 'Intermediate drilling'
    WHEN n RLIKE '(?i)(13.{0,3}3.8.{0,10}(?:casing|cas|liner)|10.{0,3}3.4.{0,10}(?:casing|cas|liner)|RIH.{0,20}(?:13|10.{0,3}3).{0,10}(?:casing|liner|cas)|running.{0,15}(?:13|10.{0,3}3).{0,10}(?:casing|liner)|ran.{0,15}(?:13|10.{0,3}3).{0,10}(?:casing|liner)|14.{0,5}(?:casing|liner).{0,5}(?:run|ran|RIH)|ran.{0,10}14.{0,5}casing|RIH.{0,15}14.{0,5}casing)' THEN 'Intermediate casing'
    WHEN n RLIKE '(?i)(12.{0,3}1.4.{0,5}(?:hole|section|BHA)|12\\.25.{0,5}(?:hole|section)|drilling.{0,15}12.{0,3}(?:1.4|25)|drilled.{0,15}12.{0,3}(?:1.4|25)|8.{0,3}1.2.{0,5}(?:hole|section|BHA)|8\\.5.{0,5}(?:hole|section)|drilling.{0,15}8.{0,3}(?:1.2|5)|drilled.{0,15}8.{0,3}(?:1.2|5)|8½.{0,5}(?:hole|section)|6.{0,3}(?:hole|section)|\\bcore.{0,10}(?:cut|no|barrel)\\b|cut core|\\bcoring\\b)' THEN 'Reservoir drilling'
    WHEN n RLIKE '(?i)(\\bliner\\b|running.{0,15}liner|RIH.{0,20}liner|landing.{0,15}liner|ran.{0,15}liner|set.{0,10}liner hanger|RIH.{0,20}casing|running.{0,15}casing|ran.{0,15}casing|P.U.{0,15}casing|9.{0,3}5.8.{0,10}(?:casing|liner|screen)|7.{0,5}liner|7.{0,5}casing|tieback.{0,15}casing|tie.back.{0,15}casing|surface tieback|ran.{0,15}tieback)' THEN 'Liner / Casing run'
    WHEN n RLIKE '(?i)(\\bcement\\b|\\bcemented\\b|\\bcementing\\b|bumped plug|displaced.{0,20}cement|pumped.{0,15}cement|mixed.{0,10}cement|bullhead.{0,10}cement|\\bWOC\\b|waiting on cement)' THEN 'Cementing'
    WHEN n RLIKE '(?i)(\\bcompletion\\b|production packer|\\bpacker\\b|\\btubing\\b|perforat|production string|\\bESP\\b|gas lift|inflow test|sand screen|gravel pack)' THEN 'Completion'
    WHEN n RLIKE '(?i)(set.{0,20}\\bplug\\b|\\bplug\\b.{0,20}set|\\bEZSV\\b|\\bEVO plug\\b|P&A|cut.{0,10}(?:casing|csg|tubing)|CUT.{0,10}(?:CASING|CSG|TUBING|TBG)|\\babandon|plug.{0,10}abandon|milling.{0,15}(?:casing|csg)|pull.{0,15}(?:casing|csg).{0,10}(?:fish|surface)|cement plug)' THEN 'P&A'
    WHEN n RLIKE '(?i)(\\blogging\\b|\\bLWD\\b|\\bMWD\\b|\\bVSP\\b|\\bwireline\\b|\\bWL\\b.{0,10}(?:log|run|RIH)|formation test|\\bDST\\b|drill stem test|\\bPLT\\b|RST log|gyro survey|\\bFIT\\b|formation integrity test|pressure point|\\bLOT\\b)' THEN 'Logging / Testing'
    WHEN n RLIKE '(?i)(\\bworkover\\b|coiled tubing|sidetrack|window.{0,15}mill|\\bwhipstock\\b)' THEN 'Workover'
    WHEN n RLIKE '(?i)(\\bWOW\\b|waiting on weather|wait.{0,15}weather|rig maintenance|general maintenance|\\bstandby\\b|wait.{0,10}parts|no crane operation|OFS strike|rig operations suspended)' THEN 'Waiting / Downtime'
    WHEN n RLIKE '(?i)(skidded rig|rig.{0,10}move|positioned rig|\\bmooring\\b|ballast|anchor.{0,10}(?:wire|chain|test)|skidded.{0,15}(?:cantilever|to well))' THEN 'Rig move / Setup'
    ELSE 'Unclassified'
  END as phase
FROM (
  SELECT *,
    REPLACE(REPLACE(REPLACE(REPLACE(sum24hr, '½', ' 1/2'), '¼', ' 1/4'), '¾', ' 3/4'), '⅛', ' 1/8') as n
  FROM workspace.default.volve_ddr_master
)