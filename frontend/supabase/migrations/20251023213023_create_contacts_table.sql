-- Create contacts table
CREATE TABLE IF NOT EXISTS "public"."contacts" (
    "id" uuid DEFAULT extensions.uuid_generate_v4() NOT NULL,
    "company_id" uuid NOT NULL,
    "rut" text NOT NULL,
    "business_name" text NOT NULL,
    "trade_name" text,
    "contact_type" text NOT NULL,
    "address" text,
    "phone" text,
    "email" text,
    "extra_data" jsonb DEFAULT '{}'::jsonb,
    "created_at" timestamp with time zone DEFAULT now() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT "contacts_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "contacts_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."companies"("id") ON DELETE CASCADE,
    CONSTRAINT "contacts_company_rut_unique" UNIQUE ("company_id", "rut"),
    CONSTRAINT "contacts_contact_type_check" CHECK (contact_type = ANY (ARRAY['provider'::text, 'client'::text, 'both'::text]))
);

-- Add comment to table
COMMENT ON TABLE "public"."contacts" IS 'Business contacts (providers, clients, or both)';

-- Add comments to columns
COMMENT ON COLUMN "public"."contacts"."contact_type" IS 'Type of contact: provider, client, or both';

-- Create indexes for better performance
CREATE INDEX "idx_contacts_company_id" ON "public"."contacts" USING btree ("company_id");
CREATE INDEX "idx_contacts_company_type" ON "public"."contacts" USING btree ("company_id", "contact_type");
CREATE INDEX "idx_contacts_rut" ON "public"."contacts" USING btree ("rut");

-- Add trigger for updated_at
CREATE TRIGGER "update_contacts_updated_at" 
    BEFORE UPDATE ON "public"."contacts" 
    FOR EACH ROW 
    EXECUTE FUNCTION "public"."update_updated_at_column"();

-- Enable RLS
ALTER TABLE "public"."contacts" ENABLE ROW LEVEL SECURITY;

-- Create RLS policies (matching the pattern from other tables)
CREATE POLICY "Users can view contacts via sessions" 
    ON "public"."contacts" 
    FOR SELECT 
    USING (
        EXISTS (
            SELECT 1 FROM "public"."sessions"
            WHERE "sessions"."company_id" = "contacts"."company_id"
            AND "sessions"."user_id" = auth.uid()
            AND "sessions"."is_active" = true
        )
    );

CREATE POLICY "Users can manage contacts via sessions" 
    ON "public"."contacts" 
    USING (
        EXISTS (
            SELECT 1 FROM "public"."sessions"
            WHERE "sessions"."company_id" = "contacts"."company_id"
            AND "sessions"."user_id" = auth.uid()
            AND "sessions"."is_active" = true
        )
    );

-- Grant permissions
GRANT ALL ON TABLE "public"."contacts" TO "anon";
GRANT ALL ON TABLE "public"."contacts" TO "authenticated";
GRANT ALL ON TABLE "public"."contacts" TO "service_role";

-- Add contact_id to sales_documents
ALTER TABLE "public"."sales_documents" 
    ADD COLUMN "contact_id" uuid,
    ADD CONSTRAINT "sales_documents_contact_id_fkey" 
        FOREIGN KEY ("contact_id") 
        REFERENCES "public"."contacts"("id") 
        ON DELETE SET NULL;

-- Add index for sales_documents.contact_id
CREATE INDEX "idx_sales_documents_contact_id" ON "public"."sales_documents" USING btree ("contact_id");

-- Add comment
COMMENT ON COLUMN "public"."sales_documents"."contact_id" IS 'Optional reference to contact (client)';

-- Add contact_id to purchase_documents
ALTER TABLE "public"."purchase_documents" 
    ADD COLUMN "contact_id" uuid,
    ADD CONSTRAINT "purchase_documents_contact_id_fkey" 
        FOREIGN KEY ("contact_id") 
        REFERENCES "public"."contacts"("id") 
        ON DELETE SET NULL;

-- Add index for purchase_documents.contact_id
CREATE INDEX "idx_purchase_documents_contact_id" ON "public"."purchase_documents" USING btree ("contact_id");

-- Add comment
COMMENT ON COLUMN "public"."purchase_documents"."contact_id" IS 'Optional reference to contact (provider)';