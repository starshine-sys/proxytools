-- Initial database schema
-- As this is intended to be mostly compatible with PluralKit, the database schema is broadly similar, although it has fewer features.

create type autoproxy_mode as enum ('OFF', 'LATCH', 'FRONT', 'MEMBER');
create type privacy as enum ('PUBLIC', 'PRIVATE');

create type proxy_tag as (
    prefix text,
    suffix text
);

create table systems (
    id          serial  primary key,
    hid         char(5) unique  not null,
    name        text,
    description text,
    tag         text,
    avatar_url  text,

    created     timestamp with time zone not null default (current_timestamp),

    description_privacy privacy not null default 'PUBLIC',
    list_privacy        privacy not null default 'PUBLIC'
);

create table members (
    id              serial  primary key,
    hid             char(5) unique  not null,
    system          int     not null    references systems (id) on delete cascade,
    colour          char(6),
    avatar_url      text,
    name            text    not null,
    display_name    text,
    description     text,
    proxy_tags      proxy_tag[] not null    default array[]::proxy_tag[],
    keep_proxy      bool        default false,

    created         timestamp with time zone  not null default (current_timestamp),

    description_privacy privacy not null default 'PUBLIC'
);

create table systems_guild (
    system  int     not null    references systems (id) on delete cascade,
    guild   bigint  not null,

    proxy_enabled       bool            not null    default true,
    autoproxy_mode      autoproxy_mode  not null    default 'OFF',
    autoproxy_member    int             references members (id) on delete set null,

    primary key (system, guild)
);

create table member_guild (
    member          int     not null references members (id) on delete cascade,
    guild           bigint  not null,
    display_name    text,

    primary key (member, guild)
);

create table if not exists accounts
(
    uid    bigint primary key,
    system serial not null references systems (id) on delete cascade
);

create table if not exists messages
(
    mid          bigint primary key,
    channel      bigint not null,
    member       serial not null references members (id) on delete cascade,
    sender       bigint not null,
    original_mid bigint
);

create table if not exists switches
(
    id        serial primary key,
    system    serial    not null references systems (id) on delete cascade,
    timestamp timestamp with time zone not null default (current_timestamp)
);

create table if not exists switch_members
(
    id      serial primary key,
    switch  serial not null references switches (id) on delete cascade,
    member  serial not null references members (id) on delete cascade
);

create table if not exists guilds
(
    id              bigint      primary key,
    log_channel     bigint,
    log_blacklist   bigint[]    not null default array[]::bigint[],
    blacklist       bigint[]    not null default array[]::bigint[]
);

create table info
(
    id              int primary key not null default 1,
    schema_version  int,

    constraint singleton check (id = 1)
);

insert into info (schema_version) values (1);
