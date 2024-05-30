vaで要件を満たすプログラミング言語の抜粋です。

```java
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;

public class Language {
	    private Map<String, Function<Object[], Object>> methods;

	        public Language() {
			        methods = new HashMap<>();
				    }

		    public void defMethod(String name, Function<Object[], Object> implementation) {
			            methods.put(name, implementation);
				        }

		        public Object callMethod(String name, Object... args) {
				        Function<Object[], Object> method = methods.get(name);
					        if (method == null) {
							            throw new RuntimeException("Method " + name + " not found");
								            }
						        return method.apply(args);
							    }

			    public static void main(String[] args) {
				            Language language = new Language();

					            language.defMethod("foo", (Object[] args) -> {
							                int x = (int) args[0];
									            int y = (int) args[1];
										                System.out.println("Foo: " + x + ", " + y);
												            return null;
													            });

						            language.defMethod("bar", (Object[] args) -> {
								                int z = (int) args[0];
										            System.out.println("Bar: " + z);
											                return null;
													        });

							            language.callMethod("foo", 1, 2); // Output: "Foo: 1, 2"
								            language.callMethod("bar", 3);    // Output: "Bar: 3"
									        }
}
```

このプログラムでは、`Language`クラスに`defMethod`メソッドと`callMethod`メソッドを定義し、`defMethod`メソッドではメソッド名と実装を受け取って、データベースとしての`methods`に保存します。`callMethod`メソッドでは、指定されたメソッド名の実装を取得し、引数を渡して実行するという仕組みです。

このような実装を使うことで、メソッドを上書きするのではなく、データベースに保存するという方法でメソッドの追加や削除ができます。
