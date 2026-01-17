#!/usr/bin/env python3
"""
Test SkillbaseService and Pydantic schemas.

Tests:
1. Schema validation (valid and invalid configs)
2. SkillbaseService CRUD operations
3. Version increment logic
4. Error handling and rollback

Author: Senior Backend Engineer
Date: 2026-01-17
"""

import sys
import asyncio
from pathlib import Path
from uuid import uuid4

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_schema_validation():
    """Test 1: Pydantic schema validation."""
    print("=" * 70)
    print("🧪 TEST 1: Pydantic Schema Validation")
    print("=" * 70)
    
    try:
        from schemas.skillbase_schemas import (
            SkillbaseConfig, ContextConfig, FlowConfig,
            AgentConfig, ToolConfig, VoiceConfig, LLMConfig,
            FlowType, StateConfig
        )
        
        # Test valid configuration
        valid_config = {
            "context": {
                "role": "Receptionist at beauty salon",
                "style": "Friendly and professional",
                "safety_rules": ["Never give medical advice"],
                "facts": ["We work 9am-9pm"]
            },
            "flow": {
                "type": "linear",
                "states": [
                    {"id": "greeting", "name": "Greeting"},
                    {"id": "inquiry", "name": "Service Inquiry"}
                ],
                "transitions": []
            },
            "agent": {
                "handoff_criteria": {"complex_request": True},
                "crm_field_mapping": {"name": "client_name"}
            },
            "tools": [
                {
                    "name": "calendar",
                    "config": {"api_url": "https://api.example.com"},
                    "enabled": True
                }
            ],
            "voice": {
                "tts_provider": "cartesia",
                "tts_voice_id": "064b17af-d36b-4bfb-b003-be07dba1b649",
                "stt_provider": "deepgram",
                "stt_language": "ru"
            },
            "llm": {
                "provider": "groq",
                "model": "llama-3.1-70b-versatile",
                "temperature": 0.7
            }
        }
        
        config = SkillbaseConfig(**valid_config)
        print("✅ Valid configuration parsed successfully")
        print(f"   - Context role: {config.context.role}")
        print(f"   - Flow type: {config.flow.type}")
        print(f"   - States: {len(config.flow.states)}")
        print(f"   - Tools: {len(config.tools)}")
        print(f"   - Voice provider: {config.voice.tts_provider}")
        print(f"   - LLM provider: {config.llm.provider}")
        
        # Test invalid configuration (missing required field)
        try:
            invalid_config = valid_config.copy()
            del invalid_config["context"]
            SkillbaseConfig(**invalid_config)
            print("❌ Should have failed on missing context")
            return False
        except Exception as e:
            print(f"✅ Correctly rejected invalid config: {type(e).__name__}")
        
        # Test flow validation (graph with invalid state reference)
        try:
            invalid_flow_config = valid_config.copy()
            invalid_flow_config["flow"] = {
                "type": "graph",
                "states": [{"id": "greeting", "name": "Greeting"}],
                "transitions": [
                    {"from_state": "greeting", "to_state": "nonexistent"}
                ]
            }
            SkillbaseConfig(**invalid_flow_config)
            print("❌ Should have failed on invalid state reference")
            return False
        except Exception as e:
            print(f"✅ Correctly rejected invalid flow: {type(e).__name__}")
        
        # Test duplicate tool names
        try:
            duplicate_tools_config = valid_config.copy()
            duplicate_tools_config["tools"] = [
                {"name": "calendar", "config": {}, "enabled": True},
                {"name": "calendar", "config": {}, "enabled": True}
            ]
            SkillbaseConfig(**duplicate_tools_config)
            print("❌ Should have failed on duplicate tool names")
            return False
        except Exception as e:
            print(f"✅ Correctly rejected duplicate tool names: {type(e).__name__}")
        
        print("\n✅ All schema validation tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Schema validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_service_operations():
    """Test 2: SkillbaseService CRUD operations."""
    print("\n" + "=" * 70)
    print("🧪 TEST 2: SkillbaseService CRUD Operations")
    print("=" * 70)
    
    try:
        from database.connection import get_async_db
        from database.models import Company
        from services.skillbase_service import SkillbaseService, SkillbaseValidationError
        
        async with get_async_db() as db:
            service = SkillbaseService(db)
            
            # Create test company
            company = Company(
                id=uuid4(),
                name="Test Company (Skillbase Service)",
                slug=f"test-sb-svc-{uuid4().hex[:8]}",
                email="test-sb-svc@example.com"
            )
            db.add(company)
            await db.flush()
            print(f"✅ Test company created: {company.id}")
            
            # Test CREATE
            valid_config = {
                "context": {
                    "role": "Test Assistant",
                    "style": "Professional",
                    "safety_rules": ["Test rule"],
                    "facts": ["Test fact"]
                },
                "flow": {
                    "type": "linear",
                    "states": [
                        {"id": "start", "name": "Start"},
                        {"id": "end", "name": "End"}
                    ],
                    "transitions": []
                },
                "agent": {
                    "handoff_criteria": {},
                    "crm_field_mapping": {}
                },
                "tools": [],
                "voice": {
                    "tts_provider": "cartesia",
                    "tts_voice_id": "test-voice-id",
                    "stt_provider": "deepgram",
                    "stt_language": "ru"
                },
                "llm": {
                    "provider": "groq",
                    "model": "llama-3.1-8b-instant",
                    "temperature": 0.7
                }
            }
            
            skillbase = await service.create(
                company_id=company.id,
                name="Test Skillbase",
                slug=f"test-sb-{uuid4().hex[:8]}",
                config=valid_config,
                description="Test description"
            )
            print(f"✅ CREATE: Skillbase created (ID: {skillbase.id}, Version: {skillbase.version})")
            
            # Test READ by ID
            fetched = await service.get_by_id(skillbase.id)
            if fetched and fetched.id == skillbase.id:
                print(f"✅ READ: Skillbase fetched by ID")
            else:
                print(f"❌ READ: Failed to fetch Skillbase")
                return False
            
            # Test READ by slug
            fetched_by_slug = await service.get_by_slug(company.id, skillbase.slug)
            if fetched_by_slug and fetched_by_slug.id == skillbase.id:
                print(f"✅ READ: Skillbase fetched by slug")
            else:
                print(f"❌ READ: Failed to fetch Skillbase by slug")
                return False
            
            # Test UPDATE (config change should increment version)
            updated_config = valid_config.copy()
            updated_config["context"]["role"] = "Updated Assistant"
            
            updated = await service.update(
                skillbase_id=skillbase.id,
                config=updated_config
            )
            
            if updated.version == 2:
                print(f"✅ UPDATE: Version incremented (v{updated.version})")
            else:
                print(f"❌ UPDATE: Version not incremented (v{updated.version})")
                return False
            
            if updated.config["context"]["role"] == "Updated Assistant":
                print(f"✅ UPDATE: Config updated correctly")
            else:
                print(f"❌ UPDATE: Config not updated")
                return False
            
            # Test LIST
            skillbases = await service.list_by_company(company.id)
            if len(skillbases) >= 1:
                print(f"✅ LIST: Found {len(skillbases)} Skillbase(s)")
            else:
                print(f"❌ LIST: No Skillbases found")
                return False
            
            # Test validation error handling
            try:
                invalid_config = {"invalid": "config"}
                await service.create(
                    company_id=company.id,
                    name="Invalid Skillbase",
                    slug=f"invalid-{uuid4().hex[:8]}",
                    config=invalid_config
                )
                print(f"❌ Should have raised SkillbaseValidationError")
                return False
            except SkillbaseValidationError:
                print(f"✅ VALIDATION: Correctly rejected invalid config")
            
            # Test DELETE
            deleted = await service.delete(skillbase.id)
            if deleted:
                print(f"✅ DELETE: Skillbase deleted")
            else:
                print(f"❌ DELETE: Failed to delete Skillbase")
                return False
            
            # Verify deletion
            fetched_after_delete = await service.get_by_id(skillbase.id)
            if fetched_after_delete is None:
                print(f"✅ DELETE: Verified Skillbase no longer exists")
            else:
                print(f"❌ DELETE: Skillbase still exists after deletion")
                return False
            
            # Cleanup
            await db.delete(company)
            await db.rollback()  # Rollback to keep DB clean
            
        print("\n✅ All service operation tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Service operation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("🚀 TESTING SKILLBASE SERVICE & SCHEMAS")
    print("=" * 70)
    print()
    
    results = []
    
    # Test 1: Schema validation (sync)
    results.append(("Schema Validation", test_schema_validation()))
    
    # Test 2: Service operations (async)
    try:
        result = asyncio.run(test_service_operations())
        results.append(("Service Operations", result))
    except Exception as e:
        print(f"❌ Failed to run async test: {e}")
        results.append(("Service Operations", False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print("\n" + "=" * 70)
    print(f"Result: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("=" * 70)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Skillbase schemas and service are ready")
        print("\n📋 Next steps:")
        print("1. Test with real database connection")
        print("2. Integrate with VoiceAgent")
        print("3. Implement SystemPromptBuilder")
        return 0
    else:
        print("\n💥 SOME TESTS FAILED!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
