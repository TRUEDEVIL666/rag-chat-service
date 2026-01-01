-- Enable Vault Extension
create extension if not exists supabase_vault with schema vault;

-- Add secret_id to ai_providers
do $$
begin
    if not exists (select 1 from information_schema.columns where table_name = 'ai_providers' and column_name = 'secret_id') then
        alter table ai_providers add column secret_id uuid references vault.secrets(id) on delete set null;
    end if;
end $$;

-- Migration skpped as api_key column does not exist
-- Existing providers will need to be updated with keys manually or via UI


-- RPC: Get Decrypted Key
create or replace function get_decrypted_provider_key(p_provider_id uuid)
returns text
language plpgsql
security definer -- Runs with privileges of creator to access vault
set search_path = public, vault
as $$
declare
    v_secret_id uuid;
    v_secret text;
begin
    select secret_id into v_secret_id from ai_providers where id = p_provider_id;
    
    if v_secret_id is null then
        return null;
    end if;

    select decrypted_secret into v_secret from vault.decrypted_secrets where id = v_secret_id;

    return v_secret;
end;
$$;

-- RPC: Create Provider Secure
create or replace function create_ai_provider_secure(
    p_name text,
    p_display_name text,
    p_base_url text,
    p_api_key text,
    p_is_active boolean
)
returns json
language plpgsql
security definer
set search_path = public, vault
as $$
declare
    v_secret_id uuid;
    v_result json;
begin
    if p_api_key is not null and p_api_key != '' then
        v_secret_id := vault.create_secret(p_api_key, p_name || '_key_' || gen_random_uuid());
    end if;

    insert into ai_providers (name, display_name, base_url, is_active, secret_id)
    values (p_name, p_display_name, p_base_url, p_is_active, v_secret_id)
    returning row_to_json(ai_providers.*) into v_result;

    return v_result;
end;
$$;

-- RPC: Update Provider Secure
create or replace function update_provider_secure(
    p_provider_id uuid,
    p_name text default null,
    p_display_name text default null,
    p_base_url text default null,
    p_api_key text default null,
    p_is_active boolean default null
)
returns json
language plpgsql
security definer
set search_path = public, vault
as $$
declare
    v_secret_id uuid;
    v_current_secret_id uuid;
    v_result json;
begin
    -- Get current secret_id
    select secret_id into v_current_secret_id from ai_providers where id = p_provider_id;

    -- Handle API Key Update
    if p_api_key is not null then
        -- Simple approach: Create new secret with unique name
        v_secret_id := vault.create_secret(p_api_key, coalesce(p_name, 'provider') || '_key_' || p_provider_id || '_' || extract(epoch from now()));
    else
        v_secret_id := v_current_secret_id;
    end if;

    update ai_providers
    set
        name = coalesce(p_name, name),
        display_name = coalesce(p_display_name, display_name),
        base_url = coalesce(p_base_url, base_url),
        is_active = coalesce(p_is_active, is_active),
        secret_id = v_secret_id
    where id = p_provider_id;

    -- Get updated row
    select row_to_json(ai_providers.*) into v_result from ai_providers where id = p_provider_id;

    return v_result;
end;
$$;
