if object_id('dbo.Master', 'u') is null

create table [dbo].[Master] (
    [id]                              bigint identity (1, 1) not null,

    [dashboardURL]                    nvarchar (255),
    [containerLabel]                  nvarchar (255),
    [containerName]                   nvarchar (255),

    [modified]                        datetime2 not null default getdate(),
    [modifiedby]                      nvarchar(50) not null default suser_name(),
    [created]                         datetime2 not null default getdate(),
    [createdby]                       nvarchar(50) not null default suser_name(),
);
