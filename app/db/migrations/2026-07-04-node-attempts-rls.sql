ALTER TABLE public.node_attempts ENABLE ROW LEVEL SECURITY;

-- Zidd's API boundary is the backend server. Learner attempt rows should never
-- be read directly through Supabase/PostgREST using anon/authenticated roles.
REVOKE ALL ON TABLE public.node_attempts FROM anon;
REVOKE ALL ON TABLE public.node_attempts FROM authenticated;
REVOKE ALL ON TABLE public.node_attempts FROM PUBLIC;
