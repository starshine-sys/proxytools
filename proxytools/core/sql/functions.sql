create function generate_hid() returns char(5) as $$
    select string_agg(substr('abcdefghijklmnopqrstuvwxyz', ceil(random() * 26)::integer, 1), '') from generate_series(1, 5)
$$ language sql volatile;


create function find_free_system_hid() returns char(5) as $$
declare new_hid char(5);
begin
    loop
        new_hid := generate_hid();
        if not exists (select 1 from systems where hid = new_hid) then return new_hid; end if;
    end loop;
end
$$ language plpgsql volatile;


create function find_free_member_hid() returns char(5) as $$
declare new_hid char(5);
begin
    loop
        new_hid := generate_hid();
        if not exists (select 1 from members where hid = new_hid) then return new_hid; end if;
    end loop;
end
$$ language plpgsql volatile;
