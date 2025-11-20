"""
End-to-End Tests for F29 Sync Service

Este archivo contiene tests E2E que prueban la sincronización de formularios F29.
Los tests verifican el flujo completo: extracción desde SII → parseo → guardado en BD.

Para ejecutar:
    pytest tests/test_f29_service_e2e.py -v

Para ejecutar con output detallado:
    pytest tests/test_f29_service_e2e.py -v -s

Para ejecutar un test específico:
    pytest tests/test_f29_service_e2e.py::TestF29Service::test_sync_f29_success -v
"""
import asyncio
import os
import pytest
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

from app.services.sii_service import SIIService
from app.config.supabase import get_supabase_client

# Configuración de tests
TEST_COMPANY_ID = os.getenv("TEST_COMPANY_ID", "eb5dc3a8-cfea-4e85-9424-e1c9e7dec097")
TEST_YEAR = os.getenv("TEST_F29_YEAR", str(datetime.now().year))

# Skip tests if no test company configured
if not TEST_COMPANY_ID:
    pytest.skip(
        "TEST_COMPANY_ID no está configurada. "
        "Configure una empresa de prueba en .env",
        allow_module_level=True
    )


@pytest.fixture
def sii_service():
    """Fixture para obtener instancia de SIIService."""
    supabase = get_supabase_client()
    return SIIService(supabase)


@pytest.fixture
def test_year():
    """Año para pruebas."""
    return TEST_YEAR


@pytest.fixture
def test_company_id():
    """ID de empresa de prueba."""
    return TEST_COMPANY_ID


# =============================================================================
# TESTS DE F29 SERVICE
# =============================================================================

class TestF29Service:
    """Tests para el servicio de sincronización F29."""

    @pytest.mark.asyncio
    async def test_sync_f29_success(
        self,
        sii_service,
        test_company_id,
        test_year
    ):
        """
        Test: Sincronización exitosa de F29 forms.

        Verifica:
        1. El servicio puede extraer F29s desde SII
        2. Los F29s se guardan correctamente en la base de datos
        3. El upsert funciona (nuevos vs actualizados)
        """
        print(f"\n🧪 Testing F29 sync for company {test_company_id}, year {test_year}")

        # Act
        result = await sii_service.sync_f29(
            company_id=test_company_id,
            year=test_year
        )

        # Assert
        assert result["success"] is True, "Sync debería ser exitoso"
        assert result["company_id"] == test_company_id, "Company ID debe coincidir"
        assert result["year"] == test_year, "Year debe coincidir"

        # Verificar estadísticas
        assert "total" in result, "Debe incluir total"
        assert "nuevos" in result, "Debe incluir nuevos"
        assert "actualizados" in result, "Debe incluir actualizados"
        assert "duration_seconds" in result, "Debe incluir duración"

        # Verificar que la suma es correcta
        total = result["total"]
        nuevos = result["nuevos"]
        actualizados = result["actualizados"]

        print(f"📊 Results:")
        print(f"   Total: {total}")
        print(f"   Nuevos: {nuevos}")
        print(f"   Actualizados: {actualizados}")
        print(f"   Duration: {result['duration_seconds']:.2f}s")

        assert nuevos + actualizados == total, "Suma de nuevos + actualizados debe ser igual a total"

        # Segunda ejecución: debería actualizar todos (no crear nuevos)
        print(f"\n🔄 Running sync again to test upsert...")

        result2 = await sii_service.sync_f29(
            company_id=test_company_id,
            year=test_year
        )

        assert result2["success"] is True, "Segunda sync debería ser exitosa"
        assert result2["total"] == total, "Total debe ser igual en segunda ejecución"
        assert result2["nuevos"] == 0, "No debería haber nuevos en segunda ejecución"
        assert result2["actualizados"] == total, "Todos deberían actualizarse en segunda ejecución"

        print(f"✅ Second run - all {result2['actualizados']} forms updated (upsert working!)")

    @pytest.mark.asyncio
    async def test_sync_f29_company_validation(
        self,
        sii_service
    ):
        """
        Test: Validación de company_id.

        Verifica que el servicio rechaza company_id inválido.
        """
        print(f"\n🧪 Testing company validation")

        # Act & Assert
        with pytest.raises(ValueError, match="Company .* not found"):
            await sii_service.sync_f29(
                company_id="00000000-0000-0000-0000-000000000000",
                year=TEST_YEAR
            )

        print("✅ Invalid company_id rejected correctly")

    @pytest.mark.asyncio
    async def test_sync_f29_credentials_validation(
        self,
        sii_service
    ):
        """
        Test: Validación de credenciales SII.

        Verifica que el servicio detecta cuando faltan credenciales.
        """
        print(f"\n🧪 Testing credentials validation")

        # Buscar una empresa sin credenciales SII
        supabase = get_supabase_client()
        companies = await supabase.companies.list_all()

        company_without_creds = None
        for company in companies:
            if not company.get("sii_password"):
                company_without_creds = company["id"]
                break

        if company_without_creds:
            # Act & Assert
            with pytest.raises(ValueError, match="has no SII credentials configured"):
                await sii_service.sync_f29(
                    company_id=company_without_creds,
                    year=TEST_YEAR
                )

            print("✅ Missing credentials detected correctly")
        else:
            pytest.skip("No company without SII credentials found for testing")

    @pytest.mark.asyncio
    async def test_sync_f29_repository_upsert(
        self,
        test_company_id
    ):
        """
        Test: Verificación directa del repository upsert.

        Verifica que el método upsert_f29_forms del repositorio funciona correctamente.
        """
        print(f"\n🧪 Testing F29Repository.upsert_f29_forms directly")

        # Arrange
        supabase = get_supabase_client()

        # Datos de prueba
        test_forms = [
            {
                "company_id": test_company_id,
                "folio": "TEST-001",
                "period": "11-2024",
                "contributor": "Test Company",
                "submission_date": "15-11-2024",
                "status": "Vigente",
                "amount": 1000000,
                "year": "2024"
            },
            {
                "company_id": test_company_id,
                "folio": "TEST-002",
                "period": "10-2024",
                "contributor": "Test Company",
                "submission_date": "15-10-2024",
                "status": "Vigente",
                "amount": 500000,
                "year": "2024"
            }
        ]

        # Act - Primera inserción
        nuevos1, actualizados1 = await supabase.f29.upsert_f29_forms(test_forms)

        # Assert primera inserción
        assert nuevos1 == 2, "Deberían ser 2 nuevos en primera inserción"
        assert actualizados1 == 0, "No debería haber actualizados en primera inserción"

        print(f"✅ First upsert: {nuevos1} nuevos, {actualizados1} actualizados")

        # Act - Segunda inserción (upsert)
        test_forms[0]["amount"] = 2000000  # Cambiar monto
        nuevos2, actualizados2 = await supabase.f29.upsert_f29_forms(test_forms)

        # Assert segunda inserción
        assert nuevos2 == 0, "No debería haber nuevos en segunda inserción"
        assert actualizados2 == 2, "Deberían actualizarse 2 en segunda inserción"

        print(f"✅ Second upsert: {nuevos2} nuevos, {actualizados2} actualizados")

        # Cleanup - Eliminar datos de prueba
        try:
            from app.config.supabase import get_supabase_client
            supabase = get_supabase_client()

            response = supabase._client.table("form29").delete().eq(
                "company_id", test_company_id
            ).in_("folio", ["TEST-001", "TEST-002"]).execute()

            print(f"🧹 Cleanup: deleted test forms")
        except Exception as e:
            print(f"⚠️  Cleanup error (non-critical): {e}")

    @pytest.mark.asyncio
    async def test_sync_f29_empty_year(
        self,
        sii_service,
        test_company_id
    ):
        """
        Test: Manejo de año sin F29 forms.

        Verifica que el servicio maneja correctamente cuando no hay F29s.
        """
        print(f"\n🧪 Testing empty year (future year)")

        # Usar un año futuro que seguramente no tiene F29s
        future_year = str(datetime.now().year + 2)

        # Act
        result = await sii_service.sync_f29(
            company_id=test_company_id,
            year=future_year
        )

        # Assert
        assert result["success"] is True, "Sync debería ser exitoso incluso sin forms"
        assert result["total"] == 0, "No debería haber forms en año futuro"
        assert result["nuevos"] == 0, "No debería haber nuevos"
        assert result["actualizados"] == 0, "No debería haber actualizados"

        print(f"✅ Empty year handled correctly: {result}")


# =============================================================================
# TESTS DE INTEGRACIÓN CON BASE DE DATOS
# =============================================================================

class TestF29DatabaseIntegration:
    """Tests de integración con la base de datos."""

    @pytest.mark.asyncio
    async def test_database_constraint_enforcement(
        self,
        test_company_id
    ):
        """
        Test: Verificación del constraint único company_id + folio.

        Verifica que la base de datos rechaza duplicados.
        """
        print(f"\n🧪 Testing database unique constraint")

        supabase = get_supabase_client()

        # Arrange - Datos duplicados
        duplicate_form = {
            "company_id": test_company_id,
            "folio": "CONSTRAINT-TEST",
            "period": "11-2024",
            "contributor": "Test",
            "submission_date": "15-11-2024",
            "status": "Vigente",
            "amount": 1000,
            "year": "2024"
        }

        # Act - Primera inserción (debería funcionar)
        try:
            response = supabase._client.table("form29").insert(duplicate_form).execute()
            assert len(response.data) > 0, "Primera inserción debería funcionar"
            print("✅ First insert successful")

            # Act - Segunda inserción directa (debería fallar con constraint)
            try:
                response2 = supabase._client.table("form29").insert(duplicate_form).execute()
                pytest.fail("Segunda inserción debería fallar por constraint único")
            except Exception as e:
                # Verificar que es error de constraint
                error_msg = str(e).lower()
                assert "unique" in error_msg or "duplicate" in error_msg, \
                    f"Debería ser error de constraint único: {e}"
                print(f"✅ Duplicate rejected correctly: {e}")

        finally:
            # Cleanup
            try:
                supabase._client.table("form29").delete().eq(
                    "company_id", test_company_id
                ).eq("folio", "CONSTRAINT-TEST").execute()
                print("🧹 Cleanup completed")
            except Exception as e:
                print(f"⚠️  Cleanup error (non-critical): {e}")

    @pytest.mark.asyncio
    async def test_get_by_folio(
        self,
        test_company_id
    ):
        """
        Test: Verificación del método get_by_folio.

        Verifica que podemos recuperar un F29 por folio.
        """
        print(f"\n🧪 Testing get_by_folio method")

        supabase = get_supabase_client()

        # Arrange - Insertar un F29 de prueba
        test_folio = f"GET-TEST-{datetime.now().timestamp()}"
        test_form = {
            "company_id": test_company_id,
            "folio": test_folio,
            "period": "11-2024",
            "contributor": "Test",
            "submission_date": "15-11-2024",
            "status": "Vigente",
            "amount": 1000,
            "year": "2024"
        }

        try:
            # Insertar
            supabase._client.table("form29").insert(test_form).execute()
            print(f"✅ Test form inserted with folio: {test_folio}")

            # Act - Buscar por folio
            found = await supabase.f29.get_by_folio(
                company_id=test_company_id,
                folio=test_folio
            )

            # Assert
            assert found is not None, "Debería encontrar el form"
            assert found["folio"] == test_folio, "Folio debe coincidir"
            assert found["company_id"] == test_company_id, "Company ID debe coincidir"

            print(f"✅ Form found successfully: {found['folio']}")

            # Act - Buscar folio inexistente
            not_found = await supabase.f29.get_by_folio(
                company_id=test_company_id,
                folio="NONEXISTENT-FOLIO"
            )

            # Assert
            assert not_found is None, "No debería encontrar folio inexistente"
            print("✅ Nonexistent folio returns None correctly")

        finally:
            # Cleanup
            try:
                supabase._client.table("form29").delete().eq(
                    "company_id", test_company_id
                ).eq("folio", test_folio).execute()
                print("🧹 Cleanup completed")
            except Exception as e:
                print(f"⚠️  Cleanup error (non-critical): {e}")


if __name__ == "__main__":
    # Permitir ejecución directa con python
    pytest.main([__file__, "-v", "-s"])
