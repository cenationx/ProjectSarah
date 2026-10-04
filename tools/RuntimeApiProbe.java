/** Headless checks: classes are loaded without initialization; no world or save is opened. */
public class RuntimeApiProbe {
    public static void main(String[] args) throws Exception {
        ClassLoader loader = RuntimeApiProbe.class.getClassLoader();
        Class<?> git = Class.forName("zombie.GitVersion", false, loader);
        for (java.lang.reflect.Field field : git.getFields()) {
            if (java.lang.reflect.Modifier.isStatic(field.getModifiers()) && field.getType() == String.class)
                System.out.println("BUILD " + field.getName() + "=" + field.get(null));
        }
        Class<?> player = Class.forName("zombie.characters.IsoPlayer", false, loader);
        int failed = 0;
        for (String name : new String[]{"setNPC", "setSceneCulled", "setForname", "setSurname"}) {
            Class<?> argument = name.equals("setNPC") || name.equals("setSceneCulled") ? boolean.class : String.class;
            try {
                System.out.println("PASS " + player.getMethod(name, argument));
            } catch (NoSuchMethodException ex) {
                System.out.println("FAIL missing public method: " + name);
                failed++;
            }
        }
        Class<?> cell = Class.forName("zombie.iso.IsoCell", false, loader);
        Class<?> desc = Class.forName("zombie.characters.SurvivorDesc", false, loader);
        System.out.println("PASS " + player.getConstructor(cell, desc, int.class, int.class, int.class));
        Class<?> factory = Class.forName("zombie.characters.SurvivorFactory", false, loader);
        Class<?> type = Class.forName("zombie.characters.SurvivorFactory$SurvivorType", false, loader);
        System.out.println("PASS " + factory.getMethod("CreateSurvivor", type, boolean.class));
        System.out.println("RESULT: " + failed + " required public API methods missing. No gameplay tested.");
        System.exit(failed == 0 ? 0 : 2);
    }
}
