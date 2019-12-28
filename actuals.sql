USE [Viewpoint]
GO

/****** Object:  StoredProcedure [dbo].[spPSC_EcoSysExtract_Cost_Actuals]    Script Date: 10/14/2019 5:15:22 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

ALTER PROCEDURE [dbo].[spPSC_EcoSysExtract_Cost_Actuals]
    @StartDate DateTime = NULL,
    @EndDate DateTime = NULL,
    @Span varchar(10) = 'id',
    @Company tinyint = NULL,
    @Job varchar(10) = NULL,
    @StartID bigint = NULL,
    @EndID bigint = NULL,
	@NullReplacement varchar(50) = NULL
as
if @Span = 'all'
BEGIN
    select @StartDate = '1/1/1990', @EndDate = DATEADD(year, 1, GETDATE());
END

if @StartDate is null
BEGIN
    select @StartDate = CONVERT(Date, DATEADD(day, -1 + iif(@Span = 'week', -7, 0), GETDATE()));    -- Grab yesterday's transactions.
END

if @EndDate is null
BEGIN
    BEGIN
        select @EndDate = case @Span when 'day' then DATEADD(SECOND, -1, DATEADD(d, 1, @StartDate))
            when 'week' then DATEADD(SECOND, -1, DATEADD(week, 1, @StartDate))
            else DATEADD(SECOND, -1, DATEADD(year, 1, GETDATE())) end   -- both 'forward' and 'all' have no end in sight.
    END
END
ELSE
BEGIN
    if convert(datetime, convert(date, @EndDate)) = @EndDate
    BEGIN
        select @EndDate = DATEADD(SECOND, -1, DATEADD(day, 1, @EndDate))
    END
END;

if @Span = 'id'
BEGIN
    if @StartID is null
    BEGIN
        select @StartID = LastJCCDKeyID + 1
        from udEcoSysData;

        if @StartID is null select @StartID=1  -- just in case there is no id in the table
    END
    if @EndID is null
    BEGIN
        Select @EndID = max(KeyID) from JCCD
    END
END;

with vwExportLines as (
select 'Project' as Project
    , 'WBSPathID' as WBSPathID
    , 'CostAccountID' as CostAccountID
    , 'ViewpointWBS' as [ViewpointWBS]
    , 'CommitmentID' as CommitmentID
    , 'Quantity' as Quantity
    , 'UOM' as UOM
    , 'Hours' as [Hours]
    , 'Cost' as [Cost]
    , 'ResourceID' as [ResourceID]
    , 'VendorID' as [VendorID]
    , 'LineID' as [LineID]
    , 'TransactionDate' as [TransactionDate]
    , 'HourType' as [HourType]
    , 'Class' as [Class]
    , 'Craft' as [Craft]
    , 'Shift' as [Shift]
    , 'InvoiceNumber' as [InvoiceNumber]
    , 'BillingNumber' as [BillingNumber]
    , 'ExternalKey' as [ExternalKey]
    --, 'TrackDateDELETE' as [TrackDate]
Union All
select distinct
    replace(iif(right(rtrim(jp.Job), 1) = '-', left(ltrim(jp.Job), len(ltrim(rtrim(jp.Job))) - 1), ltrim(rtrim(jp.Job))), ' ', '') as Project
    , replace(iif(right(rtrim(jp.Job), 1) = '-', left(ltrim(jp.Job), len(ltrim(rtrim(jp.Job))) - 1), ltrim(rtrim(jp.Job))), ' ', '') +
    '.' + coalesce(pm.udDisciplineCode, 'XX') +
--    '.' + replace(replace(iif(jp.udPhaseOverride is null, jp.Phase, left(ltrim(jp.udPhaseOverride), len(jp.udPhaseOverride) - 3) + right('000' + isnull(jp.udAreaIdentifier, ''), 3)), ' ', ''), '-', '') +
    '.' + replace(replace(jp.Phase, ' ', ''), '-', '') +
    '.' + convert(varchar(10), ct.CostType) as WBSPathID
    , convert(varchar(10), ct.CostType) as CostAccountID
    , replace(iif(right(rtrim(jp.Job), 1) = '-', left(ltrim(jp.Job), len(ltrim(rtrim(jp.Job))) - 1), ltrim(rtrim(jp.Job))), ' ', '') +
    '.' + coalesce(pm.udDisciplineCode, 'XX') +
--    '.' + replace(replace(iif(jp.udPhaseOverride is null, jp.Phase, left(ltrim(jp.udPhaseOverride), len(jp.udPhaseOverride) - 3) + right('000' + isnull(jp.udAreaIdentifier, ''), 3)), ' ', ''), '-', '') +
    '.' + replace(replace(jp.Phase, ' ', ''), '-', '') +
    '.' + convert(varchar(10), ct.CostType) as [ViewpointWBS]
    , coalesce(cd.PO, cd.SL, @NullReplacement) as CommitmentID
    , convert(varchar(20), convert(decimal(10, 2), cd.ActualUnits)) as Quantity
    , cd.UM as [UOM]
    , convert(varchar(20), cd.ActualHours) as [Hours]
    , convert(varchar(20), cd.ActualCost) as Cost
    , @NullReplacement as ResourceID
    , isnull(convert(varchar(10), cd.VendorGroup) + '-' + convert(varchar(10), cd.Vendor), @NullReplacement) as VendorID
    , isnull(convert(varchar(10), coalesce(cd.POItem, cd.SLItem)), @NullReplacement) as LineID
    , format(cd.ActualDate, 'yyyy-MM-dd') as [TransactionDate]
    , case cd.EarnFactor when 1.5 then '2' when 2.0 then '3' else '1' end as HourType
    , format(coalesce(cd.PRCo, cd.JCCo), '0') + '.' + ltrim(rtrim(cd.Craft)) + ltrim(rtrim(cd.Class)) as Class
    , format(coalesce(cd.PRCo, cd.JCCo), '0') + '.' + ltrim(rtrim(cd.Craft)) as Craft
    , isnull(convert(varchar(3), cd.[Shift]), @NullReplacement) as [Shift]
    , isnull(ltrim(rtrim(cd.APRef)), @NullReplacement) as [InvoiceNumber]
    , isnull(convert(varchar(20), cd.JBBillNumber), @NullReplacement) as [BillingNumber]
    , iif(cd.KeyID > 125000000, 'W', '') + convert(varchar(20), cd.KeyID) as ExternalKey

    --, cd.*
    --, convert(varchar(50), coalesce(bc.DateClosed, cd.PostedDate)) as TrackDate

from JCCD cd with(nolock)
    left outer join (select t.Co, max(t.KeyID) as KeyID, t.udDateCompleted, t.udJob, t.udPhase
                        from udEcoSysRefresh t
                        where t.udDateCompleted is null
                        group by t.Co, t.udDateCompleted, t.udJob, t.udPhase) esr
        on esr.udDateCompleted is null
            and esr.Co = cd.JCCo
            and esr.udJob = cd.Job
            and (esr.udPhase is null Or esr.udPhase = cd.Phase)
    inner join JCJM jm with(nolock)
        on jm.JCCo = cd.JCCo and jm.Job = cd.Job
    left outer join HQBC bc with(nolock)
        on bc.Co = cd.JCCo
            and bc.Mth = cd.Mth
            and bc.BatchId = cd.BatchId
    left outer join POIT po with(nolock)
        on cd.PO is not null
            and po.POCo = cd.JCCo
            and po.PO = cd.PO
            and po.POItem = cd.POItem
    left outer join SLIT sl with(nolock)
        on cd.SL is not null
            and sl.SLCo = cd.JCCo
            and sl.SL = cd.SL
            and sl.SLItem = cd.SLItem
    inner join JCJP jp with(nolock) on jp.JCCo = jm.JCCo and jp.Job = jm.Job
        and jp.PhaseGroup = cd.PhaseGroup and jp.Phase = cd.Phase
    left outer join JCPM pm with(nolock) on
            pm.udUniversalCoding = 'Y'
            and pm.PhaseGroup = jp.PhaseGroup
            and pm.Phase = coalesce(jp.udPhaseOverride, jp.Phase)
    inner join JCCT ct with(nolock) on ct.PhaseGroup = cd.PhaseGroup
                        and ct.CostType = case cd.CostType
                                when 12 then 11
                                when 16 then 11
                                when 14 then 17
                                when 18 then 17
                                when 25 then 20
                                when 22 then 32
                                when 23 then 32
                                when 33 then 32
                                when 36 then 32
                                when 35 then 34
                                when 40 then 34
                                when 52 then 34
                                when 61 then 34
                                when 98 then 34
                                when 42 then 45
                                else cd.CostType end
where cd.Job is not null
    and cd.Job = isnull(@Job, cd.Job)
    and cd.JCCo = isnull(@Company, cd.JCCo)
    and isnull(jm.udSyncToEcoSys, 'N') = 'Y'
    and (cd.ActualCost <> 0 or cd.ActualHours <> 0 or cd.ActualUnits <> 0)
    and (
            ( @Span = 'id' and cd.KeyID between @StartID and @EndID )
            or ( @Span <> 'id' and cd.PostedDate between @StartDate and @EndDate )
            or ( esr.KeyID is not null )
        )
)
select vwExportLines.*
from vwExportLines
order by iif(WBSPathID = 'WBSPathID', 0, 1), WBSPathID, CommitmentID, LineID

GO
