


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE EXTENSION IF NOT EXISTS "pg_net" WITH SCHEMA "extensions";






COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE OR REPLACE FUNCTION "public"."update_updated_at_column"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_updated_at_column"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."attachments" (
    "id" "text" NOT NULL,
    "name" "text" NOT NULL,
    "mime_type" "text" NOT NULL,
    "thread_id" "text",
    "upload_url" "text",
    "preview_url" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."attachments" OWNER TO "postgres";


COMMENT ON TABLE "public"."attachments" IS 'ChatKit file attachments metadata';



CREATE TABLE IF NOT EXISTS "public"."companies" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "rut" "text" NOT NULL,
    "business_name" "text" NOT NULL,
    "trade_name" "text",
    "address" "text",
    "phone" "text",
    "email" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "sii_password" "text"
);


ALTER TABLE "public"."companies" OWNER TO "postgres";


COMMENT ON TABLE "public"."companies" IS 'Basic company information (RUT, name, contact)';



COMMENT ON COLUMN "public"."companies"."sii_password" IS 'SII portal password (should be encrypted in production for security)';



CREATE TABLE IF NOT EXISTS "public"."company_tax_info" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "company_id" "uuid" NOT NULL,
    "tax_regime" "text" DEFAULT 'regimen_general'::"text" NOT NULL,
    "sii_activity_code" "text",
    "sii_activity_name" "text",
    "legal_representative_rut" "text",
    "legal_representative_name" "text",
    "start_of_activities_date" "date",
    "accounting_start_month" integer DEFAULT 1 NOT NULL,
    "extra_data" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "company_tax_info_accounting_start_month_check" CHECK ((("accounting_start_month" >= 1) AND ("accounting_start_month" <= 12))),
    CONSTRAINT "company_tax_info_tax_regime_check" CHECK (("tax_regime" = ANY (ARRAY['regimen_general'::"text", 'regimen_simplificado'::"text", 'pro_pyme'::"text", '14_ter'::"text"])))
);


ALTER TABLE "public"."company_tax_info" OWNER TO "postgres";


COMMENT ON TABLE "public"."company_tax_info" IS 'Tax-specific company information (regime, SII data)';



CREATE TABLE IF NOT EXISTS "public"."conversations" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "chatkit_session_id" "text",
    "title" "text" DEFAULT 'Nueva conversación'::"text" NOT NULL,
    "status" "text" DEFAULT 'active'::"text" NOT NULL,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "conversations_status_check" CHECK (("status" = ANY (ARRAY['active'::"text", 'archived'::"text", 'completed'::"text"])))
);


ALTER TABLE "public"."conversations" OWNER TO "postgres";


COMMENT ON TABLE "public"."conversations" IS 'ChatKit conversation threads';



CREATE TABLE IF NOT EXISTS "public"."form29" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "company_id" "uuid" NOT NULL,
    "period_year" integer NOT NULL,
    "period_month" integer NOT NULL,
    "total_sales" numeric(15,2) DEFAULT 0 NOT NULL,
    "taxable_sales" numeric(15,2) DEFAULT 0 NOT NULL,
    "exempt_sales" numeric(15,2) DEFAULT 0 NOT NULL,
    "sales_tax" numeric(15,2) DEFAULT 0 NOT NULL,
    "total_purchases" numeric(15,2) DEFAULT 0 NOT NULL,
    "taxable_purchases" numeric(15,2) DEFAULT 0 NOT NULL,
    "purchases_tax" numeric(15,2) DEFAULT 0 NOT NULL,
    "iva_to_pay" numeric(15,2) DEFAULT 0 NOT NULL,
    "iva_credit" numeric(15,2) DEFAULT 0 NOT NULL,
    "net_iva" numeric(15,2) DEFAULT 0 NOT NULL,
    "status" "text" DEFAULT 'draft'::"text" NOT NULL,
    "submission_date" timestamp with time zone,
    "folio" "text",
    "extra_data" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "form29_period_month_check" CHECK ((("period_month" >= 1) AND ("period_month" <= 12))),
    CONSTRAINT "form29_status_check" CHECK (("status" = ANY (ARRAY['draft'::"text", 'submitted'::"text"])))
);


ALTER TABLE "public"."form29" OWNER TO "postgres";


COMMENT ON TABLE "public"."form29" IS 'Monthly IVA declarations (Form 29)';



CREATE TABLE IF NOT EXISTS "public"."form29_sii_downloads" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "company_id" "uuid" NOT NULL,
    "form29_id" "uuid",
    "sii_folio" "text" NOT NULL,
    "sii_id_interno" "text",
    "period_year" integer NOT NULL,
    "period_month" integer NOT NULL,
    "period_display" "text" NOT NULL,
    "contributor_rut" "text" NOT NULL,
    "submission_date" "date",
    "status" "text" NOT NULL,
    "amount_cents" integer DEFAULT 0 NOT NULL,
    "pdf_storage_url" "text",
    "pdf_download_status" "text" DEFAULT 'pending'::"text" NOT NULL,
    "pdf_download_error" "text",
    "pdf_downloaded_at" timestamp with time zone,
    "extra_data" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "form29_sii_downloads_pdf_status_check" CHECK (("pdf_download_status" = ANY (ARRAY['pending'::"text", 'downloaded'::"text", 'error'::"text"]))),
    CONSTRAINT "form29_sii_downloads_period_month_check" CHECK ((("period_month" >= 1) AND ("period_month" <= 12))),
    CONSTRAINT "form29_sii_downloads_status_check" CHECK (("status" = ANY (ARRAY['Vigente'::"text", 'Rectificado'::"text", 'Anulado'::"text"])))
);


ALTER TABLE "public"."form29_sii_downloads" OWNER TO "postgres";


COMMENT ON TABLE "public"."form29_sii_downloads" IS 'F29 forms downloaded from SII portal (separate from locally calculated F29)';



COMMENT ON COLUMN "public"."form29_sii_downloads"."form29_id" IS 'Optional link to locally calculated F29 form (for reconciliation)';



COMMENT ON COLUMN "public"."form29_sii_downloads"."sii_folio" IS 'Folio number from SII (unique per form)';



COMMENT ON COLUMN "public"."form29_sii_downloads"."sii_id_interno" IS 'Internal SII ID required for PDF download (may be null for some forms)';



COMMENT ON COLUMN "public"."form29_sii_downloads"."amount_cents" IS 'Amount in Chilean pesos (integer, no decimals)';



COMMENT ON COLUMN "public"."form29_sii_downloads"."pdf_storage_url" IS 'URL to PDF file in storage (e.g., Supabase Storage)';



COMMENT ON COLUMN "public"."form29_sii_downloads"."pdf_download_status" IS 'Status of PDF download: pending, downloaded, or error';



CREATE TABLE IF NOT EXISTS "public"."messages" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "conversation_id" "uuid" NOT NULL,
    "user_id" "uuid" NOT NULL,
    "role" "text" NOT NULL,
    "content" "text" NOT NULL,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "messages_role_check" CHECK (("role" = ANY (ARRAY['user'::"text", 'assistant'::"text", 'system'::"text"])))
);


ALTER TABLE "public"."messages" OWNER TO "postgres";


COMMENT ON TABLE "public"."messages" IS 'Messages within ChatKit conversations';



CREATE TABLE IF NOT EXISTS "public"."profiles" (
    "id" "uuid" NOT NULL,
    "email" "text" NOT NULL,
    "full_name" "text",
    "phone" "text",
    "company_name" "text",
    "avatar_url" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "name" "text" DEFAULT ''::"text",
    "lastname" "text" DEFAULT ''::"text",
    "rol" "text" DEFAULT ''::"text",
    "phone_verified" boolean DEFAULT false NOT NULL,
    "phone_verified_at" timestamp with time zone
);


ALTER TABLE "public"."profiles" OWNER TO "postgres";


COMMENT ON TABLE "public"."profiles" IS 'User profiles extending Supabase auth.users';



COMMENT ON COLUMN "public"."profiles"."phone_verified" IS 'Whether the user''s phone number has been verified';



COMMENT ON COLUMN "public"."profiles"."phone_verified_at" IS 'Timestamp when the phone number was verified';



CREATE TABLE IF NOT EXISTS "public"."purchase_documents" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "company_id" "uuid" NOT NULL,
    "document_type" "text" NOT NULL,
    "folio" integer,
    "issue_date" "date" NOT NULL,
    "sender_rut" "text",
    "sender_name" "text",
    "net_amount" numeric(15,2) NOT NULL,
    "tax_amount" numeric(15,2) DEFAULT 0 NOT NULL,
    "exempt_amount" numeric(15,2) DEFAULT 0 NOT NULL,
    "total_amount" numeric(15,2) NOT NULL,
    "status" "text" DEFAULT 'pending'::"text" NOT NULL,
    "dte_xml" "text",
    "sii_track_id" "text",
    "file_url" "text",
    "extra_data" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "purchase_documents_document_type_check" CHECK (("document_type" = ANY (ARRAY['factura_compra'::"text", 'factura_exenta_compra'::"text", 'nota_credito_compra'::"text", 'nota_debito_compra'::"text", 'liquidacion_factura'::"text"]))),
    CONSTRAINT "purchase_documents_status_check" CHECK (("status" = ANY (ARRAY['pending'::"text", 'approved'::"text", 'rejected'::"text", 'cancelled'::"text"]))),
    CONSTRAINT "purchase_documents_total_amount_check" CHECK (("total_amount" >= (0)::numeric))
);


ALTER TABLE "public"."purchase_documents" OWNER TO "postgres";


COMMENT ON TABLE "public"."purchase_documents" IS 'Purchase documents (facturas de compra, received from suppliers)';



CREATE TABLE IF NOT EXISTS "public"."sales_documents" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "company_id" "uuid" NOT NULL,
    "document_type" "text" NOT NULL,
    "folio" integer,
    "issue_date" "date" NOT NULL,
    "recipient_rut" "text",
    "recipient_name" "text",
    "net_amount" numeric(15,2) NOT NULL,
    "tax_amount" numeric(15,2) DEFAULT 0 NOT NULL,
    "exempt_amount" numeric(15,2) DEFAULT 0 NOT NULL,
    "total_amount" numeric(15,2) NOT NULL,
    "status" "text" DEFAULT 'pending'::"text" NOT NULL,
    "dte_xml" "text",
    "sii_track_id" "text",
    "file_url" "text",
    "extra_data" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "sales_documents_document_type_check" CHECK (("document_type" = ANY (ARRAY['factura_venta'::"text", 'boleta'::"text", 'boleta_exenta'::"text", 'nota_credito_venta'::"text", 'nota_debito_venta'::"text", 'factura_exenta'::"text", 'comprobante_pago'::"text", 'liquidacion_factura'::"text"]))),
    CONSTRAINT "sales_documents_status_check" CHECK (("status" = ANY (ARRAY['pending'::"text", 'approved'::"text", 'rejected'::"text", 'cancelled'::"text"]))),
    CONSTRAINT "sales_documents_total_amount_check" CHECK (("total_amount" >= (0)::numeric))
);


ALTER TABLE "public"."sales_documents" OWNER TO "postgres";


COMMENT ON TABLE "public"."sales_documents" IS 'Sales documents (facturas de venta, issued to clients)';



CREATE TABLE IF NOT EXISTS "public"."sessions" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "company_id" "uuid" NOT NULL,
    "is_active" boolean DEFAULT true NOT NULL,
    "cookies" "jsonb" DEFAULT '{}'::"jsonb",
    "resources" "jsonb" DEFAULT '{}'::"jsonb",
    "last_accessed_at" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL
);


ALTER TABLE "public"."sessions" OWNER TO "postgres";


COMMENT ON TABLE "public"."sessions" IS 'User-company sessions (many-to-many link with cookies/resources)';



ALTER TABLE ONLY "public"."attachments"
    ADD CONSTRAINT "attachments_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."companies"
    ADD CONSTRAINT "companies_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."companies"
    ADD CONSTRAINT "companies_rut_key" UNIQUE ("rut");



ALTER TABLE ONLY "public"."company_tax_info"
    ADD CONSTRAINT "company_tax_info_company_id_key" UNIQUE ("company_id");



ALTER TABLE ONLY "public"."company_tax_info"
    ADD CONSTRAINT "company_tax_info_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."form29"
    ADD CONSTRAINT "form29_company_period_unique" UNIQUE ("company_id", "period_year", "period_month");



ALTER TABLE ONLY "public"."form29"
    ADD CONSTRAINT "form29_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."form29_sii_downloads"
    ADD CONSTRAINT "form29_sii_downloads_company_folio_unique" UNIQUE ("company_id", "sii_folio");



ALTER TABLE ONLY "public"."form29_sii_downloads"
    ADD CONSTRAINT "form29_sii_downloads_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_email_key" UNIQUE ("email");



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."purchase_documents"
    ADD CONSTRAINT "purchase_documents_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."sales_documents"
    ADD CONSTRAINT "sales_documents_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."sessions"
    ADD CONSTRAINT "sessions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."sessions"
    ADD CONSTRAINT "sessions_user_company_unique" UNIQUE ("user_id", "company_id");



ALTER TABLE ONLY "public"."purchase_documents"
    ADD CONSTRAINT "uq_purchase_documents_company_folio" UNIQUE ("company_id", "folio");



ALTER TABLE ONLY "public"."sales_documents"
    ADD CONSTRAINT "uq_sales_documents_company_folio" UNIQUE ("company_id", "folio");



CREATE INDEX "idx_profiles_phone_verified" ON "public"."profiles" USING "btree" ("phone_verified");



CREATE INDEX "idx_purchase_documents_company_date_range" ON "public"."purchase_documents" USING "btree" ("company_id", "issue_date" DESC);



CREATE INDEX "idx_purchase_documents_company_folio" ON "public"."purchase_documents" USING "btree" ("company_id", "folio");



CREATE INDEX "idx_purchase_documents_company_type_date" ON "public"."purchase_documents" USING "btree" ("company_id", "document_type", "issue_date" DESC);



CREATE INDEX "idx_purchase_documents_issue_date" ON "public"."purchase_documents" USING "btree" ("issue_date" DESC);



CREATE INDEX "idx_purchase_documents_type" ON "public"."purchase_documents" USING "btree" ("document_type");



CREATE INDEX "idx_sales_documents_company_date_range" ON "public"."sales_documents" USING "btree" ("company_id", "issue_date" DESC);



CREATE INDEX "idx_sales_documents_company_folio" ON "public"."sales_documents" USING "btree" ("company_id", "folio");



CREATE INDEX "idx_sales_documents_company_type_date" ON "public"."sales_documents" USING "btree" ("company_id", "document_type", "issue_date" DESC);



CREATE INDEX "idx_sales_documents_issue_date" ON "public"."sales_documents" USING "btree" ("issue_date" DESC);



CREATE INDEX "idx_sales_documents_type" ON "public"."sales_documents" USING "btree" ("document_type");



CREATE INDEX "ix_form29_company_period" ON "public"."form29" USING "btree" ("company_id", "period_year", "period_month");



CREATE INDEX "ix_form29_sii_downloads_company_period" ON "public"."form29_sii_downloads" USING "btree" ("company_id", "period_year", "period_month");



CREATE INDEX "ix_form29_sii_downloads_folio" ON "public"."form29_sii_downloads" USING "btree" ("sii_folio");



CREATE INDEX "ix_form29_sii_downloads_pdf_status" ON "public"."form29_sii_downloads" USING "btree" ("company_id", "pdf_download_status") WHERE ("pdf_download_status" = 'pending'::"text");



CREATE INDEX "ix_form29_sii_downloads_status" ON "public"."form29_sii_downloads" USING "btree" ("company_id", "status");



CREATE INDEX "ix_form29_sii_downloads_unlinked" ON "public"."form29_sii_downloads" USING "btree" ("company_id", "period_year", "period_month") WHERE ("form29_id" IS NULL);



CREATE INDEX "ix_purchase_documents_company_date" ON "public"."purchase_documents" USING "btree" ("company_id", "issue_date");



CREATE INDEX "ix_purchase_documents_company_type" ON "public"."purchase_documents" USING "btree" ("company_id", "document_type");



CREATE INDEX "ix_sales_documents_company_date" ON "public"."sales_documents" USING "btree" ("company_id", "issue_date");



CREATE INDEX "ix_sales_documents_company_type" ON "public"."sales_documents" USING "btree" ("company_id", "document_type");



CREATE INDEX "ix_sessions_company_active" ON "public"."sessions" USING "btree" ("company_id", "is_active");



CREATE INDEX "ix_sessions_user_company" ON "public"."sessions" USING "btree" ("user_id", "company_id");



CREATE OR REPLACE TRIGGER "update_attachments_updated_at" BEFORE UPDATE ON "public"."attachments" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_companies_updated_at" BEFORE UPDATE ON "public"."companies" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_company_tax_info_updated_at" BEFORE UPDATE ON "public"."company_tax_info" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_conversations_updated_at" BEFORE UPDATE ON "public"."conversations" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_form29_sii_downloads_updated_at" BEFORE UPDATE ON "public"."form29_sii_downloads" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_form29_updated_at" BEFORE UPDATE ON "public"."form29" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_profiles_updated_at" BEFORE UPDATE ON "public"."profiles" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_purchase_documents_updated_at" BEFORE UPDATE ON "public"."purchase_documents" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_sales_documents_updated_at" BEFORE UPDATE ON "public"."sales_documents" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_sessions_updated_at" BEFORE UPDATE ON "public"."sessions" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



ALTER TABLE ONLY "public"."company_tax_info"
    ADD CONSTRAINT "company_tax_info_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."companies"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."conversations"
    ADD CONSTRAINT "conversations_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."form29"
    ADD CONSTRAINT "form29_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."companies"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."form29_sii_downloads"
    ADD CONSTRAINT "form29_sii_downloads_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."companies"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."form29_sii_downloads"
    ADD CONSTRAINT "form29_sii_downloads_form29_id_fkey" FOREIGN KEY ("form29_id") REFERENCES "public"."form29"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_conversation_id_fkey" FOREIGN KEY ("conversation_id") REFERENCES "public"."conversations"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."profiles"
    ADD CONSTRAINT "profiles_id_fkey" FOREIGN KEY ("id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."purchase_documents"
    ADD CONSTRAINT "purchase_documents_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."companies"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."sales_documents"
    ADD CONSTRAINT "sales_documents_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."companies"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."sessions"
    ADD CONSTRAINT "sessions_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."companies"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."sessions"
    ADD CONSTRAINT "sessions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "public"."profiles"("id") ON DELETE CASCADE;



CREATE POLICY "Users can create messages in own conversations" ON "public"."messages" FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM "public"."conversations"
  WHERE (("conversations"."id" = "messages"."conversation_id") AND ("conversations"."user_id" = "auth"."uid"())))));



CREATE POLICY "Users can delete form29 sii downloads via sessions" ON "public"."form29_sii_downloads" FOR DELETE USING ((EXISTS ( SELECT 1
   FROM "public"."sessions"
  WHERE (("sessions"."company_id" = "form29_sii_downloads"."company_id") AND ("sessions"."user_id" = "auth"."uid"()) AND ("sessions"."is_active" = true)))));



CREATE POLICY "Users can delete own sessions" ON "public"."sessions" FOR DELETE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can insert form29 sii downloads via sessions" ON "public"."form29_sii_downloads" FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM "public"."sessions"
  WHERE (("sessions"."company_id" = "sessions"."company_id") AND ("sessions"."user_id" = "auth"."uid"()) AND ("sessions"."is_active" = true)))));



CREATE POLICY "Users can insert own profile" ON "public"."profiles" FOR INSERT WITH CHECK (("auth"."uid"() = "id"));



CREATE POLICY "Users can insert own sessions" ON "public"."sessions" FOR INSERT WITH CHECK (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can manage form29 via sessions" ON "public"."form29" USING ((EXISTS ( SELECT 1
   FROM "public"."sessions"
  WHERE (("sessions"."company_id" = "form29"."company_id") AND ("sessions"."user_id" = "auth"."uid"()) AND ("sessions"."is_active" = true)))));



CREATE POLICY "Users can manage own conversations" ON "public"."conversations" USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can manage purchase documents via sessions" ON "public"."purchase_documents" USING ((EXISTS ( SELECT 1
   FROM "public"."sessions"
  WHERE (("sessions"."company_id" = "purchase_documents"."company_id") AND ("sessions"."user_id" = "auth"."uid"()) AND ("sessions"."is_active" = true)))));



CREATE POLICY "Users can manage sales documents via sessions" ON "public"."sales_documents" USING ((EXISTS ( SELECT 1
   FROM "public"."sessions"
  WHERE (("sessions"."company_id" = "sales_documents"."company_id") AND ("sessions"."user_id" = "auth"."uid"()) AND ("sessions"."is_active" = true)))));



CREATE POLICY "Users can update companies via sessions" ON "public"."companies" FOR UPDATE USING ((EXISTS ( SELECT 1
   FROM "public"."sessions"
  WHERE (("sessions"."company_id" = "companies"."id") AND ("sessions"."user_id" = "auth"."uid"()) AND ("sessions"."is_active" = true)))));



CREATE POLICY "Users can update company tax info via sessions" ON "public"."company_tax_info" FOR UPDATE USING ((EXISTS ( SELECT 1
   FROM "public"."sessions"
  WHERE (("sessions"."company_id" = "company_tax_info"."company_id") AND ("sessions"."user_id" = "auth"."uid"()) AND ("sessions"."is_active" = true)))));



CREATE POLICY "Users can update form29 sii downloads via sessions" ON "public"."form29_sii_downloads" FOR UPDATE USING ((EXISTS ( SELECT 1
   FROM "public"."sessions"
  WHERE (("sessions"."company_id" = "form29_sii_downloads"."company_id") AND ("sessions"."user_id" = "auth"."uid"()) AND ("sessions"."is_active" = true)))));



CREATE POLICY "Users can update own profile" ON "public"."profiles" FOR UPDATE USING (("auth"."uid"() = "id"));



CREATE POLICY "Users can update own sessions" ON "public"."sessions" FOR UPDATE USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view companies via sessions" ON "public"."companies" FOR SELECT USING ((EXISTS ( SELECT 1
   FROM "public"."sessions"
  WHERE (("sessions"."company_id" = "companies"."id") AND ("sessions"."user_id" = "auth"."uid"()) AND ("sessions"."is_active" = true)))));



CREATE POLICY "Users can view company tax info via sessions" ON "public"."company_tax_info" FOR SELECT USING ((EXISTS ( SELECT 1
   FROM "public"."sessions"
  WHERE (("sessions"."company_id" = "company_tax_info"."company_id") AND ("sessions"."user_id" = "auth"."uid"()) AND ("sessions"."is_active" = true)))));



CREATE POLICY "Users can view form29 sii downloads via sessions" ON "public"."form29_sii_downloads" FOR SELECT USING ((EXISTS ( SELECT 1
   FROM "public"."sessions"
  WHERE (("sessions"."company_id" = "form29_sii_downloads"."company_id") AND ("sessions"."user_id" = "auth"."uid"()) AND ("sessions"."is_active" = true)))));



CREATE POLICY "Users can view form29 via sessions" ON "public"."form29" FOR SELECT USING ((EXISTS ( SELECT 1
   FROM "public"."sessions"
  WHERE (("sessions"."company_id" = "form29"."company_id") AND ("sessions"."user_id" = "auth"."uid"()) AND ("sessions"."is_active" = true)))));



CREATE POLICY "Users can view messages from own conversations" ON "public"."messages" FOR SELECT USING ((EXISTS ( SELECT 1
   FROM "public"."conversations"
  WHERE (("conversations"."id" = "messages"."conversation_id") AND ("conversations"."user_id" = "auth"."uid"())))));



CREATE POLICY "Users can view own conversations" ON "public"."conversations" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view own profile" ON "public"."profiles" FOR SELECT USING (("auth"."uid"() = "id"));



CREATE POLICY "Users can view own sessions" ON "public"."sessions" FOR SELECT USING (("auth"."uid"() = "user_id"));



CREATE POLICY "Users can view purchase documents via sessions" ON "public"."purchase_documents" FOR SELECT USING ((EXISTS ( SELECT 1
   FROM "public"."sessions"
  WHERE (("sessions"."company_id" = "purchase_documents"."company_id") AND ("sessions"."user_id" = "auth"."uid"()) AND ("sessions"."is_active" = true)))));



CREATE POLICY "Users can view sales documents via sessions" ON "public"."sales_documents" FOR SELECT USING ((EXISTS ( SELECT 1
   FROM "public"."sessions"
  WHERE (("sessions"."company_id" = "sales_documents"."company_id") AND ("sessions"."user_id" = "auth"."uid"()) AND ("sessions"."is_active" = true)))));



ALTER TABLE "public"."companies" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."company_tax_info" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."conversations" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."form29" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."form29_sii_downloads" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."messages" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."profiles" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."purchase_documents" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."sales_documents" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."sessions" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";





GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";

























































































































































GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "anon";
GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "authenticated";
GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "service_role";


















GRANT ALL ON TABLE "public"."attachments" TO "anon";
GRANT ALL ON TABLE "public"."attachments" TO "authenticated";
GRANT ALL ON TABLE "public"."attachments" TO "service_role";



GRANT ALL ON TABLE "public"."companies" TO "anon";
GRANT ALL ON TABLE "public"."companies" TO "authenticated";
GRANT ALL ON TABLE "public"."companies" TO "service_role";



GRANT ALL ON TABLE "public"."company_tax_info" TO "anon";
GRANT ALL ON TABLE "public"."company_tax_info" TO "authenticated";
GRANT ALL ON TABLE "public"."company_tax_info" TO "service_role";



GRANT ALL ON TABLE "public"."conversations" TO "anon";
GRANT ALL ON TABLE "public"."conversations" TO "authenticated";
GRANT ALL ON TABLE "public"."conversations" TO "service_role";



GRANT ALL ON TABLE "public"."form29" TO "anon";
GRANT ALL ON TABLE "public"."form29" TO "authenticated";
GRANT ALL ON TABLE "public"."form29" TO "service_role";



GRANT ALL ON TABLE "public"."form29_sii_downloads" TO "anon";
GRANT ALL ON TABLE "public"."form29_sii_downloads" TO "authenticated";
GRANT ALL ON TABLE "public"."form29_sii_downloads" TO "service_role";



GRANT ALL ON TABLE "public"."messages" TO "anon";
GRANT ALL ON TABLE "public"."messages" TO "authenticated";
GRANT ALL ON TABLE "public"."messages" TO "service_role";



GRANT ALL ON TABLE "public"."profiles" TO "anon";
GRANT ALL ON TABLE "public"."profiles" TO "authenticated";
GRANT ALL ON TABLE "public"."profiles" TO "service_role";



GRANT ALL ON TABLE "public"."purchase_documents" TO "anon";
GRANT ALL ON TABLE "public"."purchase_documents" TO "authenticated";
GRANT ALL ON TABLE "public"."purchase_documents" TO "service_role";



GRANT ALL ON TABLE "public"."sales_documents" TO "anon";
GRANT ALL ON TABLE "public"."sales_documents" TO "authenticated";
GRANT ALL ON TABLE "public"."sales_documents" TO "service_role";



GRANT ALL ON TABLE "public"."sessions" TO "anon";
GRANT ALL ON TABLE "public"."sessions" TO "authenticated";
GRANT ALL ON TABLE "public"."sessions" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";































RESET ALL;
