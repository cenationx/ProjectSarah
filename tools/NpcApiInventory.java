public class NpcApiInventory {
    public static void main(String[] args) throws Exception {
        for (String name : new String[]{"zombie.characters.IsoPlayer", "zombie.characters.IsoSurvivor", "zombie.characters.SurvivorDesc", "zombie.iso.IsoCell", "zombie.core.Core"}) {
            Class<?> c = Class.forName(name, false, NpcApiInventory.class.getClassLoader());
            System.out.println("CLASS " + name);
            for (java.lang.reflect.Constructor<?> ctor : c.getConstructors()) System.out.println(ctor);
            for (java.lang.reflect.Method m : c.getMethods()) {
                if (m.getName().matches("(?i).*(npc|surviv|pathfind|update|playernum|instance|forename|surname|version|removefrom|addtomoving|character|localplayer).*") || m.getName().equals("isDead")) System.out.println(m);
            }
        }
    }
}
