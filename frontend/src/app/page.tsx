"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createBrowserClient } from "@supabase/ssr";
import { Navbar } from "@/components/features/landing/navbar";
import { Hero } from "@/components/features/landing/hero";
import { ThreeCs } from "@/components/features/landing/three-cs";
import { Features } from "@/components/features/landing/features";
import { FAQ } from "@/components/features/landing/faq";
import { CTA } from "@/components/features/landing/cta";
import { LandingFooter } from "@/shared/ui/branding/LandingFooter";
import { ContactDialog } from "@/components/features/landing/contact-dialog";

export default function Landing() {
  const [isContactDialogOpen, setIsContactDialogOpen] = useState(false);
  const router = useRouter();

  const supabase = createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  );

  useEffect(() => {
    const checkUser = async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (user) {
        router.push("/dashboard");
      }
    };

    checkUser();
  }, [router, supabase.auth]);

  const handleContactSales = () => {
    setIsContactDialogOpen(true);
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <Navbar />
      <Hero onContactSales={handleContactSales} />
      <ThreeCs />
      <Features />
      <FAQ />
      <CTA onContactSales={handleContactSales} />
      <LandingFooter />
      <ContactDialog
        isOpen={isContactDialogOpen}
        onClose={() => setIsContactDialogOpen(false)}
      />
    </main>
  );
}
