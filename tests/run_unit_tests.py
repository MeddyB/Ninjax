"""
Script pour exécuter tous les tests unitaires des services principaux
"""
import sys
import subprocess
import os
from pathlib import Path


def run_tests():
    """Exécute tous les tests unitaires"""
    print("🧪 Exécution des tests unitaires pour les services principaux")
    print("=" * 60)
    
    # Définir les groupes de tests
    test_groups = {
        "Services": [
            "tests/test_services/test_token_service.py",
            "tests/test_services/test_windows_service.py", 
            "tests/test_services/test_api_proxy_service.py"
        ],
        "Modèles de données": [
            "tests/test_data_models/test_token_model.py",
            "tests/test_data_models/test_service_model.py"
        ],
        "Utilitaires": [
            "tests/test_utils/test_file_utils.py",
            "tests/test_utils/test_validation.py"
        ],
        "Configuration": [
            "tests/test_core/test_config.py"
        ]
    }
    
    total_passed = 0
    total_failed = 0
    failed_groups = []
    
    for group_name, test_files in test_groups.items():
        print(f"\n📋 Tests {group_name}")
        print("-" * 40)
        
        group_passed = 0
        group_failed = 0
        
        for test_file in test_files:
            if not os.path.exists(test_file):
                print(f"⚠️  Fichier de test non trouvé: {test_file}")
                continue
            
            print(f"🔍 Exécution: {test_file}")
            
            try:
                # Exécuter pytest pour ce fichier spécifique
                result = subprocess.run([
                    sys.executable, "-m", "pytest", 
                    test_file, 
                    "-v", 
                    "--tb=short",
                    "--no-header"
                ], capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    # Extraire le nombre de tests passés
                    output_lines = result.stdout.split('\n')
                    summary_line = [line for line in output_lines if 'passed' in line and '=' in line]
                    if summary_line:
                        print(f"✅ {summary_line[-1].strip()}")
                        # Essayer d'extraire le nombre
                        try:
                            passed_count = int(summary_line[-1].split()[0])
                            group_passed += passed_count
                        except:
                            group_passed += 1
                    else:
                        print("✅ Tests passés")
                        group_passed += 1
                else:
                    print(f"❌ Échec des tests")
                    if result.stdout:
                        print("Sortie:", result.stdout[-500:])  # Dernières 500 chars
                    if result.stderr:
                        print("Erreur:", result.stderr[-500:])
                    group_failed += 1
                    
            except subprocess.TimeoutExpired:
                print(f"⏰ Timeout pour {test_file}")
                group_failed += 1
            except Exception as e:
                print(f"💥 Erreur lors de l'exécution de {test_file}: {e}")
                group_failed += 1
        
        print(f"📊 Résumé {group_name}: {group_passed} passés, {group_failed} échoués")
        
        total_passed += group_passed
        total_failed += group_failed
        
        if group_failed > 0:
            failed_groups.append(group_name)
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📈 RÉSUMÉ FINAL")
    print("=" * 60)
    print(f"✅ Total tests passés: {total_passed}")
    print(f"❌ Total tests échoués: {total_failed}")
    
    if failed_groups:
        print(f"⚠️  Groupes avec échecs: {', '.join(failed_groups)}")
    
    success_rate = (total_passed / (total_passed + total_failed)) * 100 if (total_passed + total_failed) > 0 else 0
    print(f"📊 Taux de réussite: {success_rate:.1f}%")
    
    if total_failed == 0:
        print("🎉 Tous les tests sont passés!")
        return True
    else:
        print("⚠️  Certains tests ont échoué")
        return False


def run_specific_test_group(group_name):
    """Exécute un groupe spécifique de tests"""
    test_groups = {
        "services": [
            "tests/test_services/test_token_service.py",
            "tests/test_services/test_windows_service.py", 
            "tests/test_services/test_api_proxy_service.py"
        ],
        "models": [
            "tests/test_data_models/test_token_model.py",
            "tests/test_data_models/test_service_model.py"
        ],
        "utils": [
            "tests/test_utils/test_file_utils.py",
            "tests/test_utils/test_validation.py"
        ],
        "config": [
            "tests/test_core/test_config.py"
        ]
    }
    
    if group_name.lower() not in test_groups:
        print(f"❌ Groupe de tests '{group_name}' non trouvé")
        print(f"Groupes disponibles: {', '.join(test_groups.keys())}")
        return False
    
    test_files = test_groups[group_name.lower()]
    
    print(f"🧪 Exécution des tests {group_name}")
    print("=" * 40)
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"🔍 Exécution: {test_file}")
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file, 
                "-v"
            ])
            if result.returncode != 0:
                return False
        else:
            print(f"⚠️  Fichier non trouvé: {test_file}")
    
    return True


def main():
    """Point d'entrée principal"""
    if len(sys.argv) > 1:
        group_name = sys.argv[1]
        success = run_specific_test_group(group_name)
    else:
        success = run_tests()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()